import requests

from flask import Blueprint, request, current_app, Response, jsonify, redirect

from geonature.utils.env import DB
from geonature.core.users.models import VUserslistForallMenu, BibOrganismes, CorRole
from pypnusershub.db.models import User
from pypnusershub.db.models_register import TempUser
from pypnusershub.routes_register import bp as user_api

from geonature.utils.utilssqlalchemy import json_resp
from geonature.core.gn_permissions import decorators as permissions
from geonature.core.gn_meta.models import CorDatasetActor, TDatasets
from geonature.core.gn_meta.repositories import get_datasets_cruved


routes = Blueprint("users", __name__)
s = requests.Session()
config = current_app.config


@routes.route("/menu/<int:id_menu>", methods=["GET"])
@json_resp
def getRolesByMenuId(id_menu):
    """
        Retourne la liste des roles associés à un menu

        Parameters
        ----------
         - nom_complet : début du nom complet du role
    """
    q = DB.session.query(VUserslistForallMenu).filter_by(id_menu=id_menu)

    parameters = request.args
    if parameters.get("nom_complet"):
        q = q.filter(
            VUserslistForallMenu.nom_complet.ilike(
                "{}%".format(parameters.get("nom_complet"))
            )
        )
    data = q.order_by(VUserslistForallMenu.nom_complet.asc()).all()
    return [n.as_dict() for n in data]


@routes.route("/role/<int:id_role>", methods=["GET"])
@json_resp
def get_role(id_role):
    """
        Retourne le détail d'un role
    """
    user = DB.session.query(User).filter_by(id_role=id_role).one()
    return user.as_dict()


@routes.route("/role", methods=["POST"])
@json_resp
def insert_role(user=None):
    """
        Insert un role
        @TODO : Ne devrait pas être là mais dans UserHub
        Utilisé dans l'authentification du CAS INPN
    """
    if user:
        data = user
    else:
        data = dict(request.get_json())
    user = User(**data)
    if user.id_role is not None:
        exist_user = DB.session.query(User).get(user.id_role)
        if exist_user:
            DB.session.merge(user)
        else:
            DB.session.add(user)
    else:
        DB.session.add(user)
    DB.session.commit()
    DB.session.flush()
    return user.as_dict()


@routes.route("/login/recovery", methods=["POST"])
def login_recovery():
    """
        Inscrit un user à partir de l'interface geonature
        Fonctionne selon l'autorisation 'ENABLE_SIGN_UP' dans la config.
        Fait appel à l'API UsersHub
    """
    #test des droits
    if (not config.get('ENABLE_SIGN_UP', False)):
        return jsonify({"msg": "Page introuvable"}), 404
    
    data = request.get_json()

    r = s.post(url=config['API_ENDPOINT'] + "/pypn/register/post_usershub/login_recovery", json=data)

    return Response(r), r.status_code


@routes.route("/password/recovery", methods=["POST"])
def password_recovery():
    """
        Inscrit un user à partir de l'interface geonature
        Fonctionne selon l'autorisation 'ENABLE_SIGN_UP' dans la config.
        Fait appel à l'API UsersHub
    """
    #test des droits
    if (not config.get('ENABLE_SIGN_UP', False)):
        return jsonify({"msg": "Page introuvable"}), 404

    data = request.get_json()

    identifiant = data.get('identifiant', None)

    if not identifiant:
        return {'msg': "Login inconnu"}, 400
    
    user = DB.session.query(User).filter_by(identifiant=identifiant).one()

    data = {"email": user.email, 
            "url_confirmation": config['URL_APPLICATION'] + "/#/new-password"}

    r = s.post(url=config['API_ENDPOINT'] + "/pypn/register/post_usershub/password_recovery", json=data)

    return Response(r), r.status_code
    

@routes.route("/inscription", methods=["POST"])
def inscription():
    """
        Inscrit un user à partir de l'interface geonature
        Fonctionne selon l'autorisation 'ENABLE_SIGN_UP' dans la config.
        Fait appel à l'API UsersHub
    """
    #test des droits
    if (not config.get('ENABLE_SIGN_UP', False)):
        return jsonify({"message": "Page introuvable"}), 404

    data = request.get_json()
    #ajout des valeurs non présentes dans le form
    data['groupe'] = False
    data['url_confirmation'] = config['API_ENDPOINT'] + "/users/confirmation"

    r = s.post(url=config['API_ENDPOINT'] + "/pypn/register/post_usershub/create_temp_user", json=data)

    return Response(r), r.status_code


@routes.route("/confirmation", methods=["GET"])
def confirmation():
    """
        Confirmation du mail
        Fait appel à l'API UsersHub
    """
    #test des droits
    if (not config.get('ENABLE_SIGN_UP', False)):
        return jsonify({"message": "Page introuvable"}), 404

    token = request.args.get('token', None)
    if token is None:
        return jsonify({"message": "Token introuvable"}), 404

    data = {"token": token, "id_application": config['ID_APPLICATION_GEONATURE']}

    r = s.post(url=config['API_ENDPOINT'] + "/pypn/register/post_usershub/valid_temp_user", json=data)
    if r.status_code != 200:
        return Response(r), r.status_code

    role = r.json()
    #Creation d'un JDD pour le l'utilisateur
    dataset = TDatasets(
        id_acquisition_framework=65,
        dataset_name="Données personnelles "+role['prenom_role'].title()+" "+role['nom_role'].title(),
        dataset_shortname="Données personnelles",
        dataset_desc="Données personnelles de "+role['prenom_role'].title()+" "+role['nom_role'].title(),
        id_nomenclature_data_type=325,
        keywords="",
        marine_domain=True,
        terrestrial_domain=True,
        id_nomenclature_dataset_objectif=443,
        id_nomenclature_collecting_method=402,
        id_nomenclature_data_origin=77,
        id_nomenclature_source_status=75,
        id_nomenclature_resource_type=323,
        default_validity=True,
        active=True
    )
    cor_dataset_actor = CorDatasetActor(
        id_role=role['id_role'],
        id_nomenclature_actor_role=370
    )
    dataset.cor_dataset_actor.append(cor_dataset_actor)

    DB.session.add(dataset)
    DB.session.commit()
    DB.session.flush()

    return redirect(config['URL_APPLICATION'], code=302)


@routes.route("/role", methods=["PUT"])
@permissions.check_cruved_scope("R", True)
@json_resp
def update_role(info_role):
    """
        Modifie le role de l'utilisateur du token en cours
    """
    data = dict(request.get_json())

    user = DB.session.query(User).get(info_role.id_role)

    if user is None:
        return {"message": "Droit insuffisant"}, 403

    attliste = [k for k in data]
    for att in attliste:
        if not getattr(User, att, False):
            data.pop(att)

    #liste des attributs qui ne doivent pas être modifiable par l'user
    black_list_att_update = [
        'active', 
        'date_insert', 
        'date_update', 
        'groupe', 
        'id_organisme', 
        'id_role', 
        'pass_plus', 
        'pn', 
        'uuid_role'
    ]
    for key, value in data.items():
        if key not in black_list_att_update:
            setattr(user, key, value)

    DB.session.merge(user)
    DB.session.commit()
    DB.session.flush()
    return user.as_dict()


def set_change_password(data):
    if not data.get('password', None) or not data.get('password_confirmation', None) or not data.get('token', None):
        return {"msg": "Erreur serveur"}, 500

    r = s.post(url=config['API_ENDPOINT'] + "/pypn/register/post_usershub/change_password", json=data)

    if r.status_code != 200:
        #comme concerne le password, on explicite pas le message
        return {"msg": "Erreur serveur"}, 500

    return {"msg": "Mot de passe modifié avec succès"}, 200


@routes.route("/password/change", methods=["POST"])
@json_resp
def change_password():
    """
        Modifie le mot de passe de l'utilisateur du token
        Fait appel à l'API UsersHub
    """
    if (not config.get('ENABLE_SIGN_UP', False)):
        return {"message": "Page introuvable"}, 404

    data = request.get_json()
    
    return set_change_password(data)


@routes.route("/password", methods=["PUT"])
@permissions.check_cruved_scope("R", True)
@json_resp
def update_password(info_role):
    """
        Modifie le mot de passe de l'utilisateur connecté
        Fait appel à l'API UsersHub
    """
    if (not config.get('ENABLE_SIGN_UP', False)):
        return {"message": "Page introuvable"}, 404

    data = request.get_json()
    user = DB.session.query(User).get(info_role.id_role)
    
    if user is None:
        return {"msg": "Droit insuffisant"}, 403

    #Vérification du password initiale du role
    if not user.check_password(data.get('init_password', None)):
        return {"msg": "Le mot de passe initial est invalide"}, 400

    #recuperation du token usershub API
    token = s.post(url=config['API_ENDPOINT'] + "/pypn/register/post_usershub/create_cor_role_token", json={'email': user.email}).json()

    data['token'] = token['token']
    
    return set_change_password(data)
    

@routes.route("/cor_role", methods=["POST"])
@json_resp
def insert_in_cor_role(id_group=None, id_user=None):
    """
        Insert une correspondante role groupe
        c-a-d permet d'attacher un role à un groupe
       # TODO ajouter test sur les POST de données
    """
    exist_user = (
        DB.session.query(CorRole)
        .filter(CorRole.id_role_groupe == id_group)
        .filter(CorRole.id_role_utilisateur == id_user)
        .all()
    )
    if not exist_user:
        cor_role = CorRole(id_group, id_user)
        DB.session.add(cor_role)
        DB.session.commit()
        DB.session.flush()
        return cor_role.as_dict()
    return {"message": "cor already exists"}, 500


@routes.route("/organism", methods=["POST"])
@json_resp
def insert_organism(organism):
    """
        Insert un organisme
    """
    if organism is not None:
        data = organism
    else:
        data = dict(request.get_json())
    organism = BibOrganismes(**data)
    if organism.id_organisme:
        exist_org = DB.session.query(BibOrganismes).get(organism.id_organisme)
        if exist_org:
            DB.session.merge(organism)
        else:
            DB.session.add(organism)
    else:
        DB.session.add(organism)
    DB.session.commit()
    DB.session.flush()
    return organism.as_dict()


@routes.route("/roles", methods=["GET"])
@json_resp
def get_roles():
    """
        Retourne tous les roles
    """
    params = request.args
    q = DB.session.query(User)
    if "group" in params:
        q = q.filter(User.groupe == params["group"])
    return [user.as_dict() for user in q.all()]


@routes.route("/organisms", methods=["GET"])
@json_resp
def get_organismes():
    """
        Retourne tous les organismes
    """
    organisms = DB.session.query(BibOrganismes).all()
    return [organism.as_dict() for organism in organisms]


@routes.route("/organisms_dataset_actor", methods=["GET"])
@permissions.check_cruved_scope("R", True)
@json_resp
def get_organismes_jdd(info_role):
    """
        Retourne tous les organismes qui sont acteurs dans un JDD
        et dont l'utilisateur a des droit sur ce JDD (via son CRUVED)
    """

    datasets = [dataset["id_dataset"] for dataset in get_datasets_cruved(info_role)]
    organisms = (
        DB.session.query(BibOrganismes)
        .join(
            CorDatasetActor, BibOrganismes.id_organisme == CorDatasetActor.id_organism
        )
        .filter(CorDatasetActor.id_dataset.in_(datasets))
        .distinct(BibOrganismes.id_organisme)
        .all()
    )
    return [organism.as_dict() for organism in organisms]
