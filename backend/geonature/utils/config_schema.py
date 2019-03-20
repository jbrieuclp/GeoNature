"""
    Description des options de configuration
"""

import os

from marshmallow import Schema, fields, validates_schema, ValidationError
from marshmallow.validate import OneOf, Regexp
from geonature.core.gn_synthese.synthese_config import (
    DEFAULT_EXPORT_COLUMNS,
    DEFAULT_LIST_COLUMN,
    DEFAULT_COLUMNS_API_SYNTHESE,
)
from geonature.utils.env import GEONATURE_VERSION


class CasUserSchemaConf(Schema):
    URL = fields.Url(missing="https://inpn.mnhn.fr/authentication/information")
    ID = fields.String(missing="mon_id")
    PASSWORD = fields.String(missing="mon_pass")


class CasFrontend(Schema):
    CAS_AUTHENTIFICATION = fields.Boolean(missing="false")
    CAS_URL_LOGIN = fields.Url(missing="https://preprod-inpn.mnhn.fr/auth/login")
    CAS_URL_LOGOUT = fields.Url(missing="https://preprod-inpn.mnhn.fr/auth/logout")


class CasSchemaConf(Schema):
    CAS_URL_VALIDATION = fields.String(
        missing="https://preprod-inpn.mnhn.fr/auth/serviceValidate"
    )
    CAS_USER_WS = fields.Nested(CasUserSchemaConf, missing=dict())
    USERS_CAN_SEE_ORGANISM_DATA = fields.Boolean(missing=False)


class BddConfig(Schema):
    id_area_type_municipality = fields.Integer(missing=25)
    ID_USER_SOCLE_1 = fields.Integer(missing=8)
    ID_USER_SOCLE_2 = fields.Integer(missing=6)


class RightsSchemaConf(Schema):
    NOTHING = fields.Integer(missing=0)
    MY_DATA = fields.Integer(missing=1)
    MY_ORGANISM_DATA = fields.Integer(missing=2)
    ALL_DATA = fields.Integer(missing=3)


class MailErrorConf(Schema):
    MAIL_ON_ERROR = fields.Boolean(missing=False)
    MAIL_HOST = fields.String(missing="")
    HOST_PORT = fields.Integer(missing=465)
    MAIL_FROM = fields.String(missing="")
    MAIL_USERNAME = fields.String(missing="")
    MAIL_PASS = fields.String(missing="")
    MAIL_TO = fields.List(fields.String(), missing=list())


# class a utiliser pour les paramètres que l'on ne veut pas passer au frontend
class GnPySchemaConf(Schema):
    SQLALCHEMY_DATABASE_URI = fields.String(
        required=True,
        validate=Regexp(
            "^postgresql:\/\/.*:.*@[^:]+:\w+\/\w+$",
            0,
            """Database uri is invalid ex:
             postgresql://monuser:monpass@server:port/db_name""",
        ),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = fields.Boolean(missing=False)
    SESSION_TYPE = fields.String(missing="filesystem")
    SECRET_KEY = fields.String(required=True)
    # le cookie expire toute les 7 jours par défaut
    COOKIE_EXPIRATION = fields.Integer(missing=3600 * 24 * 7)
    COOKIE_AUTORENEW = fields.Boolean(missing=True)
    TRAP_ALL_EXCEPTIONS = fields.Boolean(missing=False)

    UPLOAD_FOLDER = fields.String(missing="static/medias")
    BASE_DIR = fields.String(
        missing=os.path.dirname(
            os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
        )
    )
    MAILERROR = fields.Nested(MailErrorConf, missing=dict())
    CAS = fields.Nested(CasSchemaConf, missing=dict())


class GnFrontEndConf(Schema):
    PROD_MOD = fields.Boolean(missing=True)
    DISPLAY_FOOTER = fields.Boolean(missing=True)
    DISPLAY_STAT_BLOC = fields.Boolean(missing=True)
    DISPLAY_MAP_LAST_OBS = fields.Boolean(missing=True)
    MULTILINGUAL = fields.Boolean(missing=False)


id_municipality = BddConfig().load({}).data.get("id_area_type_municipality")


class Synthese(Schema):
    AREA_FILTERS = fields.List(
        fields.Dict, missing=[{"label": "Communes", "id_type": id_municipality}]
    )
    # Listes des champs renvoyés par l'API synthese '/synthese'
    # Si on veut afficher des champs personnalisés dans le frontend (paramètre LIST_COLUMNS_FRONTEND) il faut
    # d'abbord s'assurer que ces champs sont bien renvoyé par l'API !
    # Champs disponibles: tous ceux de la vue 'v_synthese_for_web_app
    COLUMNS_API_SYNTHESE_WEB_APP = fields.List(
        fields.String, missing=DEFAULT_COLUMNS_API_SYNTHESE
    )
    # Colonnes affichées sur la liste des résultats de la sytnthese
    LIST_COLUMNS_FRONTEND = fields.List(fields.Dict, missing=DEFAULT_LIST_COLUMN)
    EXPORT_COLUMNS = fields.List(fields.String(), missing=DEFAULT_EXPORT_COLUMNS)
    # Certaines colonnes sont obligatoires pour effectuer les filtres CRUVED
    EXPORT_ID_SYNTHESE_COL = fields.String(missing="idSynthese")
    EXPORT_ID_DATASET_COL = fields.String(missing="jddId")
    EXPORT_ID_DIGITISER_COL = fields.String(missing="id_digitiser")
    EXPORT_OBSERVERS_COL = fields.String(missing="observer")
    EXPORT_GEOJSON_4326_COL = fields.String(missing="geojson_4326")
    EXPORT_GEOJSON_LOCAL_COL = fields.String(missing="geojson_local")
    EXPORT_METADATA_ID_DATASET_COL = fields.String(missing="jdd_id")
    EXPORT_METADATA_ACTOR_COL = fields.String(missing="acteurs")
    EXPORT_FORMAT = fields.List(
        fields.String(), missing=["csv", "geojson", "shapefile"]
    )
    # Nombre de résultat à afficher pour la rechercher autocompleté de taxon
    TAXON_RESULT_NUMBER = fields.Integer(missing=20)
    # Liste des id attributs Taxhub à afficher sur la fiche détaile de la synthese
    # et sur les filtres taxonomiques avancés
    ID_ATTRIBUT_TAXHUB = fields.List(fields.Integer(), missing=[102, 103])
    # nom des colonnes de la table gn_synthese.synthese que l'on veux retirer des filres dynamiques
    # et de la modale d'information détaillée d'une observation
    # example = "[non_digital_proof]"
    EXCLUDED_COLUMNS = fields.List(fields.String(), missing=[])
    # Afficher ou non l'arbre taxonomique
    DISPLAY_TAXON_TREE = fields.Boolean(missing=True)
    # rajoute le filtre sur l'observers_txt en ILIKE sur les portée 1 et 2 du CRUVED
    CRUVED_SEARCH_WITH_OBSERVER_AS_TXT = fields.Boolean(missing=False)
    # Nombre max d'observation à afficher sur la carte
    NB_MAX_OBS_MAP = fields.Integer(missing=50000)
    # clusteriser les layers sur la carte
    ENABLE_LEAFLET_CLUSTER = fields.Boolean(missing=True)
    # Nombre max d'observation dans les exports
    NB_MAX_OBS_EXPORT = fields.Integer(missing=50000)
    # Nombre des "dernières observations" affiché à l'arrive sur la synthese
    NB_LAST_OBS = fields.Integer(missing=100)


# On met la valeur par défaut de DISCONECT_AFTER_INACTIVITY inferieure à COOKIE_EXPIRATION
cookie_expiration = GnPySchemaConf().load({}).data.get("COOKIE_EXPIRATION")


# Map configuration
BASEMAP = [
    {
        "name": "OpenStreetMap",
        "layer": "//{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
        "attribution": "&copy OpenStreetMap",
    },
    {
        "name": "OpenTopoMap",
        "layer": "//a.tile.opentopomap.org/{z}/{x}/{y}.png",
        "attribution": "© OpenTopoMap",
    },
    {
        "name": "GoogleSatellite",
        "layer": "//{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "subdomains": ["mt0", "mt1", "mt2", "mt3"],
        "attribution": "© GoogleMap",
    },
]


class MapConfig(Schema):
    BASEMAP = fields.List(fields.Dict, missing=BASEMAP)
    CENTER = fields.List(fields.Float, missing=[46.52863469527167, 2.43896484375])
    ZOOM_LEVEL = fields.Integer(missing=6)
    ZOOM_LEVEL_RELEVE = fields.Integer(missing=15)
    # zoom appliqué sur la carte lorsque l'on clique sur une liste
    # ne s'applique qu'aux points
    ZOOM_ON_CLICK = fields.Integer(missing=18)


# class a utiliser pour les paramètres que l'on veut passer au frontend
class GnGeneralSchemaConf(Schema):
    appName = fields.String(missing="GeoNature2")
    GEONATURE_VERSION = fields.String(missing=GEONATURE_VERSION.strip())
    DEFAULT_LANGUAGE = fields.String(missing="fr")
    PASS_METHOD = fields.String(missing="hash", validate=OneOf(["hash", "md5"]))
    DEBUG = fields.Boolean(missing=False)
    URL_APPLICATION = fields.Url(required=True)
    API_ENDPOINT = fields.Url(required=True)
    API_TAXHUB = fields.Url(required=True)
    LOCAL_SRID = fields.Integer(required=True, missing=2154)
    ID_APPLICATION_GEONATURE = fields.Integer(missing=3)
    XML_NAMESPACE = fields.String(missing="{http://inpn.mnhn.fr/mtd}")
    MTD_API_ENDPOINT = fields.Url(missing="https://preprod-inpn.mnhn.fr/mtd")
    CAS_PUBLIC = fields.Nested(CasFrontend, missing=dict())
    RIGHTS = fields.Nested(RightsSchemaConf, missing=dict())
    FRONTEND = fields.Nested(GnFrontEndConf, missing=dict())
    SYNTHESE = fields.Nested(Synthese, missing=dict())
    MAPCONFIG = fields.Nested(MapConfig, missing=dict())
    # Ajoute la surchouche 'taxonomique' sur l'API nomenclature
    ENABLE_NOMENCLATURE_TAXONOMIC_FILTERS = fields.Boolean(missing=True)
    BDD = fields.Nested(BddConfig, missing=dict())


class ManifestSchemaConf(Schema):
    package_format_version = fields.String(required=True)
    module_code = fields.String(required=True)
    module_version = fields.String(required=True)
    min_geonature_version = fields.String(required=True)
    max_geonature_version = fields.String(required=True)
    exclude_geonature_versions = fields.List(fields.String)


class ManifestSchemaProdConf(Schema):
    module_code = fields.String(required=True)
