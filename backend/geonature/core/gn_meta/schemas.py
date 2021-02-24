from geonature.utils.env import MA
from marshmallow import pre_load, fields
from .models import TDatasets, TAcquisitionFramework, CorAcquisitionFrameworkActor, CorDatasetActor
from pypnusershub.db.models import User
from geonature.core.users.models import BibOrganismes
from pypnnomenclature.models import TNomenclatures


class UserSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = (
            "_password",
            "_password_plus",
            "active",
            "date_insert",
            "date_update",
            "desc_role",
            "email",
            "groupe",
            "remarques",
            "identifiant",
        )

    nom_complet = fields.Function(
        lambda obj: (obj.nom_role if obj.nom_role else "")
        + (" " + obj.prenom_role if obj.prenom_role else "")
    )

    @pre_load
    def make_observer(self, data, **kwargs):
        if isinstance(data, int):
            return dict({"id_role": data})
        return data

class OrganismeSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = BibOrganismes
        load_instance = True

class NomenclatureSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TNomenclatures
        load_instance = True

class DatasetActorSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = CorDatasetActor
        load_instance = True
        include_fk = True

    role = MA.Nested(UserSchema, dump_only=True)
    nomenclature_actor_role = MA.Nested(NomenclatureSchema, dump_only=True)
    organism = MA.Nested(OrganismeSchema, dump_only=True)

class DatasetSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TDatasets
        load_instance = True
        include_fk = True

    cor_dataset_actor = MA.Nested(
        DatasetActorSchema,
        many=True
    )
    creator = MA.Nested(UserSchema, dump_only=True)
    cruved = fields.Method("get_user_cruved")

    def get_user_cruved(self, obj):
    	return obj.get_object_cruved(self.context['info_role'], self.context['user_cruved'])


class AcquisitionFrameworkActorSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = CorAcquisitionFrameworkActor
        load_instance = True
        include_fk = True

    role = MA.Nested(UserSchema, dump_only=True)
    nomenclature_actor_role = MA.Nested(NomenclatureSchema, dump_only=True)
    organism = MA.Nested(OrganismeSchema, dump_only=True)


class AcquisitionFrameworkSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TAcquisitionFramework
        load_instance = True
        include_fk = True

    t_datasets = MA.Nested(DatasetSchema, many=True)
    cor_af_actor = MA.Nested(
        AcquisitionFrameworkActorSchema,
        many=True
    )
    creator = MA.Nested(UserSchema, dump_only=True)
    cruved = fields.Method("get_user_cruved")

    def get_user_cruved(self, obj):
    	return obj.get_object_cruved(self.context['info_role'], self.context['user_cruved'])