from .database import db
from datetime import datetime


class Medicament(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(255), nullable=False)
    demandes = db.relationship('Demande', backref='medicament', lazy=True)

    def __repr__(self):
        return f"Medicament(id={self.id}, nom={self.nom})"


class Demande(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    medicament_id = db.Column(db.Integer, db.ForeignKey('medicament.id'), nullable=False)
    quantite_demandee = db.Column(db.Integer, nullable=False)
    date_demande = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    commandes = db.relationship('Commande', backref='demande', lazy=True, cascade="all,delete")

    def __repr__(self):
        return f"Demande(id={self.id}, medicament_id={self.medicament_id}, quantite_demandee={self.quantite_demandee}, date_demande={self.date_demande})"
class Commande(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    demande_id = db.Column(db.Integer, db.ForeignKey('demande.id'), nullable=False)
    quantite_commandee = db.Column(db.Integer, nullable=True)
    fournisseur = db.Column(db.String(255), nullable=True)
    date_commande = db.Column(db.DateTime, nullable=True)
    observation = db.Column(db.String(255), nullable=True, default='')

    def __repr__(self):
        return f"Commande(id={self.id}, demande_id={self.demande_id}, quantite_commandee={self.quantite_commandee}, fournisseur={self.fournisseur}, date_commande={self.date_commande})"


class Archive(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    medicament_id = db.Column(db.Integer, db.ForeignKey('medicament.id'), nullable=False)
    medicament = db.relationship('Medicament', backref='archives')
    quantite_demandee_archive = db.Column(db.Integer, nullable=False)
    observation = db.Column(db.String(255), nullable=True)
    date_demande_archive = db.Column(db.DateTime, nullable=False)
    quantite_commandee_archive = db.Column(db.Integer, nullable=False)
    fournisseur_archive = db.Column(db.String(255), nullable=False)
    date_commande_archive = db.Column(db.DateTime, nullable=False)
    date_archive = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Archive(id={self.id}, medicament_id={self.medicament_id}, quantite_demandee_archive={self.quantite_demandee_archive}, date_demande_archive={self.date_demande_archive}, quantite_commandee_archive={self.quantite_commandee_archive}, fournisseur_archive={self.fournisseur_archive}, date_commande_archive={self.date_commande_archive})"f"Archive(id={self.id}, medicament_id={self.medicament_id}, demande_id={self.demande_id}, commande_id={self.commande_id}, date_archive={self.date_archive}, quantite_demandee_archive={self.quantite_demandee_archive}, date_demande_archive={self.date_demande_archive}, quantite_commandee_archive={self.quantite_commandee_archive}, fournisseur_archive={self.fournisseur_archive}, date_commande_archive={self.date_commande_archive})"


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(255), nullable=False)
    demandes = db.relationship('Demande_article', backref='article', lazy=True)

    def __repr__(self):
        return f"Article(id={self.id}, nom={self.nom})"

class Demande_article(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    quantite_demandee = db.Column(db.Integer, nullable=False)
    date_demande = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    commandes = db.relationship('Commande_article', backref='demande_article', lazy=True, cascade="all,delete")

    def __repr__(self):
        return f"Demande_article(id={self.id}, article_id={self.article_id}, quantite_demandee={self.quantite_demandee}, date_demande={self.date_demande})"

class Commande_article(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    demande_article_id = db.Column(db.Integer, db.ForeignKey('demande_article.id'), nullable=False)
    quantite_commandee = db.Column(db.Integer, nullable=True)
    fournisseur = db.Column(db.String(255), nullable=True)
    date_commande = db.Column(db.DateTime, nullable=True)
    observation = db.Column(db.String(255), nullable=True, default='')

    def __repr__(self):
        return f"Commande_article(id={self.id}, demande_article_id={self.demande_article_id}, quantite_commandee={self.quantite_commandee}, fournisseur={self.fournisseur}, date_commande={self.date_commande})"

class Archive_article(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    article = db.relationship('Article', backref='archives_articles')
    quantite_demandee_archive = db.Column(db.Integer, nullable=False)
    observation = db.Column(db.String(255), nullable=True)
    date_demande_archive = db.Column(db.DateTime, nullable=False)
    quantite_commandee_archive = db.Column(db.Integer, nullable=False)
    fournisseur_archive = db.Column(db.String(255), nullable=False)
    date_commande_archive = db.Column(db.DateTime, nullable=False)
    date_archive = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Archive_article(id={self.id}, article_id={self.article_id}, quantite_demandee_archive={self.quantite_demandee_archive}, date_demande_archive={self.date_demande_archive}, quantite_commandee_archive={self.quantite_commandee_archive}, fournisseur_archive={self.fournisseur_archive}, date_commande_archive={self.date_commande_archive})"