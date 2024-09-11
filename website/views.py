import os
from urllib.parse import urlparse

import subprocess
from flask import current_app

import pytz
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, send_file
from werkzeug.utils import secure_filename

from .models import Medicament, Demande, Commande, Archive, Commande_article, Archive_article, Article, Demande_article
from .database import db
from datetime import datetime, timedelta
from dateutil import tz

from .upload import UploadForm

main = Blueprint('main', __name__)

algeria_tz = tz.gettz('Africa/Algiers')

@main.route('/')
def index():
    demandes = Demande.query.order_by(Demande.date_demande.desc()).all()
    return render_template('index.html',pytz=pytz, algeria_tz=algeria_tz, active_page ='home',demandes=demandes)

@main.route('/search_medicaments', methods=['GET'])
def search_medicaments():
    search = request.args.get('search')
    medicaments = Medicament.query.filter(Medicament.nom.like(f'%{search}%')).all()
    return jsonify([medicament.nom for medicament in medicaments])

@main.route('/add_demande', methods=['POST'])
def add_demande():
    medicament_name = request.form.get('medicament')
    quantity = int(request.form.get('quantity_needed'), 0)
    confirm_order = request.form.get('confirm_order')

    if not medicament_name:
        return "Error: Medicament name is required", 400

    if not quantity:
        return "Error: Quantity is required", 400

    medicament = Medicament.query.filter_by(nom=medicament_name).first()

    if not medicament:
        medicament = Medicament(nom=medicament_name)
        db.session.add(medicament)
        db.session.commit()

    # Check if a demande for the same medicament has been made in the last 24 hours
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    recent_demande = Demande.query.filter_by(medicament_id=medicament.id).filter(Demande.date_demande >= one_day_ago).first()

    if recent_demande and not confirm_order:
        return jsonify({
                           "error": f"{recent_demande.quantite_demandee} {medicament_name} ont déjà été demander le : {recent_demande.date_demande.strftime('%d/%m/%Y')}"}), 409

    if recent_demande and confirm_order:
        # If the user confirmed the order, add the new quantity to the existing demande and update the date
        recent_demande.quantite_demandee += quantity
        recent_demande.date_demande = datetime.utcnow()
    else:
        # If there is no recent demande, create a new one
        demande = Demande(medicament_id=medicament.id, quantite_demandee=quantity)
        db.session.add(demande)
        db.session.commit()  # Commit the Demande to the database here

        # Create a new Commande for the new Demande
        commande = Commande(demande_id=demande.id)
        db.session.add(commande)

    db.session.commit()

    # Get the referrer URL
    referrer = request.referrer
    if referrer:
        # Parse the URL to get only the path
        referrer_path = urlparse(referrer).path
        # Redirect to the referrer page
        return redirect(referrer_path)
    else:
        # If there is no referrer, redirect to 'index' as default
        return redirect(url_for('main.index'))

@main.route('/commande')
def commande():
    commandes = Commande.query.all()
    return render_template('indexcommande.html', pytz=pytz, algeria_tz=algeria_tz,commandes=commandes, active_page='commande')

@main.route('/archive_commande/<int:commande_id>', methods=['POST'])
def archive_commande(commande_id):
    fournisseur = request.form.get('fournisseur')
    quantite = int(request.form.get('quantite')) if fournisseur != "MANQUANT" else 0
    observation = request.form.get('observation')

    commande = Commande.query.get(commande_id)
    if commande:
        if fournisseur != "MANQUANT":
            # Créer une nouvelle archive
            archive = Archive(
                medicament_id=commande.demande.medicament_id,
                quantite_demandee_archive=commande.demande.quantite_demandee,
                date_demande_archive=commande.demande.date_demande,
                quantite_commandee_archive=quantite,
                fournisseur_archive=fournisseur,
                date_commande_archive=datetime.utcnow(),
                observation=observation
            )
            db.session.add(archive)
        else:
            # Si le fournisseur est "MANQUANT", mettre à jour le fournisseur dans la table Commande
            commande.fournisseur = "MANQUANT"

        # Vérifier si la quantité commandée est inférieure à la quantité demandée
        if quantite < commande.demande.quantite_demandee:
            # Si c'est le cas, mettre à jour la quantité demandée avec la quantité restante
            commande.demande.quantite_demandee -= quantite
        elif fournisseur != "MANQUANT":
            # Sinon, supprimer la demande
            db.session.delete(commande.demande)

        db.session.commit()
        return "Commande mise à jour ou supprimée", 200
    else:
        return "Erreur : Commande non trouvée", 404

@main.route('/delete_demande/<int:demande_id>', methods=['GET'])
def delete_demande(demande_id):
    demande = Demande.query.get(demande_id)
    if demande:
        db.session.delete(demande)
        db.session.commit()
        return redirect(url_for('main.index'))
    else:
        return "Error: Record not found", 404


@main.route('/modifier_demande/<int:demande_id>', methods=['POST'])
def modifier_demande(demande_id):
    demande = Demande.query.get(demande_id)
    if demande:
        new_quantity = int(request.form.get('new_quantity'))
        demande.quantite_demandee = new_quantity
        db.session.commit()
        flash('La demande a été modifiée avec succès.', 'success')
        return redirect(url_for('main.index'))
    else:
        flash('Erreur : Demande non trouvée', 'error')
        return redirect(url_for('main.index'))


@main.route('/archive')
def archive():
    archives = Archive.query.all()
    return render_template('indexarchive.html', pytz=pytz, algeria_tz=algeria_tz,archives=archives, active_page='archive')

@main.route('/delete_archive', methods=['POST'])
def delete_archive():
    archive_ids = request.form.getlist('archive_ids')
    for archive_id in archive_ids:
        archive = Archive.query.get(archive_id)
        if archive:
            db.session.delete(archive)
    db.session.commit()
    return redirect(url_for('main.archive'))


@main.route('/modifier_archive/<int:archive_id>', methods=['POST'])
def modifier_archive(archive_id):
    archive = Archive.query.get(archive_id)
    if archive:
        new_quantity = int(request.form.get('new_quantity'))
        archive.quantite_commandee_archive = new_quantity
        db.session.commit()
        flash('L\'archive a été modifiée avec succès.', 'success')
        return redirect(url_for('main.archive'))
    else:
        flash('Erreur : Archive non trouvée', 'error')
        return redirect(url_for('main.archive'))




# Cotee article

@main.route('/article')
def article():
    demandes = Demande_article.query.order_by(Demande_article.date_demande.desc()).all()
    return render_template('indexarticle.html', pytz=pytz, algeria_tz=algeria_tz,demandes=demandes, active_page='article')

@main.route('/search_articles', methods=['GET'])
def search_articles():
    search = request.args.get('search')
    articles = Article.query.filter(Article.nom.like(f'%{search}%')).all()
    return jsonify([article.nom for article in articles])


@main.route('/add_demande_article', methods=['POST'])
def add_demande_article():
    article_name = request.form.get('article')
    quantity = int(request.form.get('quantity_needed_article') or 0)
    confirm_order = request.form.get('confirm_order')

    if not article_name:
        return "Error: Article name is required", 400

    if quantity is None:
        return "Error: Quantity is required", 400

    article = Article.query.filter_by(nom=article_name).first()

    if not article:
        article = Article(nom=article_name)
        db.session.add(article)
        db.session.commit()

    demande = Demande_article(article_id=article.id, quantite_demandee=quantity)
    db.session.add(demande)
    db.session.commit()

    commande = Commande_article(demande_article_id=demande.id)
    db.session.add(commande)
    db.session.commit()

    referrer = request.referrer
    if referrer:
        referrer_path = urlparse(referrer).path
        return redirect(referrer_path)
    else:
        return redirect(url_for('main.article'))


@main.route('/commande_article')
def commande_article():
    commandes = Commande_article.query.all()
    return render_template('indexcommandearticle.html', pytz=pytz, algeria_tz=algeria_tz,commandes=commandes, active_page='commande_article')

@main.route('/archive_commande_article/<int:commande_article_id>', methods=['POST'])
def archive_commande_article(commande_article_id):
    fournisseur = request.form.get('fournisseur')
    quantite = int(request.form.get('quantite'))
    observation = request.form.get('observation')

    commande = Commande_article.query.get(commande_article_id)
    if commande:
        archive = Archive_article(
            article_id=commande.demande_article.article_id,
            quantite_demandee_archive=commande.demande_article.quantite_demandee,
            date_demande_archive=commande.demande_article.date_demande,
            quantite_commandee_archive=quantite,
            fournisseur_archive=fournisseur,
            date_commande_archive=datetime.utcnow(),
            observation=observation
        )
        db.session.add(archive)
        if quantite < commande.demande_article.quantite_demandee:
            commande.demande_article.quantite_demandee -= quantite
        else:
            db.session.delete(commande.demande_article)
        db.session.commit()
        return "Commande archivée et demande supprimée", 200
    else:
        return "Erreur : Commande non trouvée", 404

@main.route('/delete_demande_article/<int:demande_article_id>', methods=['GET'])
def delete_demande_article(demande_article_id):
    demande = Demande_article.query.get(demande_article_id)
    if demande:
        db.session.delete(demande)
        db.session.commit()
        return redirect(url_for('main.article'))
    else:
        return "Error: Record not found", 404

@main.route('/modifier_demande_article/<int:demande_article_id>', methods=['POST'])
def modifier_demande_article(demande_article_id):
    demande = Demande_article.query.get(demande_article_id)
    if demande:
        new_quantity = int(request.form.get('new_quantity'))
        demande.quantite_demandee = new_quantity
        db.session.commit()
        flash('La demande a été modifiée avec succès.', 'success')
        return redirect(url_for('main.article'))
    else:
        flash('Erreur : Demande non trouvée', 'error')
        return redirect(url_for('main.article'))

@main.route('/archive_article')
def archive_article():
    archives = Archive_article.query.all()
    return render_template('indexarchivearticle.html', pytz=pytz, algeria_tz=algeria_tz,archives=archives, active_page='archive_article')

@main.route('/delete_archive_articles', methods=['POST'])
def delete_archive_articles():
    archive_article_ids = request.form.getlist('archive_article_ids')
    for archive_article_id in archive_article_ids:
        archive = Archive_article.query.get(archive_article_id)
        if archive:
            db.session.delete(archive)
    db.session.commit()
    return redirect(url_for('main.archive_article'))

@main.route('/modifier_archive_article/<int:archive_article_id>', methods=['POST'])
def modifier_archive_article(archive_article_id):
    archive = Archive_article.query.get(archive_article_id)
    if archive:
        new_quantity = int(request.form.get('new_quantity'))
        archive.quantite_commandee_archive = new_quantity
        db.session.commit()
        flash('L\'archive a été modifiée avec succès.', 'success')
        return redirect(url_for('main.archive_article'))
    else:
        flash('Erreur : Archive non trouvée', 'error')
        return redirect(url_for('main.archive_article'))

@main.route('/gardes')
def gardes():
    gardes = [
        "Jour de l’an (1er Janvier)",
        "05 Janvier",
        "12 Janvier",
        "19 Janvier",
        "26 Janvier",
        "02 Février",
        "09 Février",
        "16 Février",
        "23 Février",
        "01 Mars",
        "08 Mars",
        "15 Mars",
        "22 Mars",
        "29 Mars",
        "05 Avril",
        "Premier jour de l’Aïd El Fitr (Avril)",
        "Deuxième jour de l’Aïd El Fitr (Avril)",
        "12 Avril",
        "19 Avril",
        "26 Avril",
        "Fête du Travail (1er Mai)",
        "03 Mai",
        "10 Mai",
        "17 Mai",
        "24 Mai",
        "31 Mai",
        "07 Juin",
        "14 Juin",
        "Premier jour de l’Aïd El Adha (Juin)",
        "Deuxième jour de l’Aïd El Adha (Juin)",
        "Troisième jour de l’Aïd El Adha (Juin)",
        "21 Juin",
        "28 Juin"
    ]
    return render_template('gardes.html', gardes=gardes, active_page='gardes')

@main.route('/download_garde/<date>', methods=['GET'])
def download_garde(date):
    date = date.replace(' ', '_')
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, 'static', 'gardes', f"{date}.docx")
    absolute_path = os.path.abspath(file_path)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "Fichier non trouvé", 404

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404




@main.route('/upload', methods=['POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        f = form.file.data
        filename = secure_filename(f.filename)
        file_path = os.path.realpath('C:\\AppPharmaciePapa\\Reste des logiciels\\updateArticles\\database.mdb')

        # Check if the file exists and delete it if it does
        if os.path.exists(file_path):
            os.remove(file_path)

        # Save the new file
        f.save(file_path)

        # Execute the updateArticles.py script
        script_path = os.path.realpath('C:\\AppPharmaciePapa\\Reste des logiciels\\updateArticles\\updateArticles.py')
        result = subprocess.run(['python', script_path], stdout=subprocess.PIPE)

        # Log the output of the script
        current_app.logger.info(result.stdout)

        return redirect(url_for('main.update'))
    return 'Failed to upload file'


@main.route('/update')
def update():
    form = UploadForm()
    return render_template('update.html', update=update, active_page='update', form=form)
