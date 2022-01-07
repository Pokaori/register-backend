from __main__ import app_api
from flask_restx import fields, reqparse

parser = reqparse.RequestParser()
parser.add_argument('registration_code', type=str, location='form', help="Registartion code in format x.x.xx",
                    required=True)
parser.add_argument('id_domains', type=int, location='form', required=True)
parser.add_argument('name', type=str, location='form', required=True)
parser.add_argument('year_creation', type=int, location='form', required=True)
parser.add_argument('year_making_changes', type=int, location='form')
parser.add_argument('year_termination_application', type=int, location='form')
parser.add_argument('date_of_decision_on_state_registration', type=str, location='form', required=True)
parser.add_argument('date_of_decision_on_state_registration_of_changes', type=str, location='form')
parser.add_argument('date_of_decision_to_terminate_the_application', type=str, location='form')
parser.add_argument('doc_copy_of_method', type=reqparse.FileStorage, location='files', required=True)
parser.add_argument('doc_report_review', type=reqparse.FileStorage, location='files', required=True)
parser.add_argument('doc_certificate_of_approbation', type=reqparse.FileStorage, location='files', required=True)
parser.add_argument('doc_copy_of_implementation', type=reqparse.FileStorage, location='files', required=True)
parser.add_argument('doc_discount_card', type=reqparse.FileStorage, location='files', required=True)
parser.add_argument('author', type=str, location='form', help="Second name and initials of method author",
                    required=True)

method_put = reqparse.RequestParser()
# method_put.add_argument('id', type=int, location='form', required=True)
method_put.add_argument('registration_code', type=str, location='form', help="Registartion code in format x.x.xx")
method_put.add_argument('id_domains', type=int, location='form')
method_put.add_argument('name', type=str, location='form')
method_put.add_argument('year_creation', type=int, location='form')
method_put.add_argument('year_making_changes', type=int, location='form')
method_put.add_argument('year_termination_application', type=int, location='form')
method_put.add_argument('date_of_decision_on_state_registration', type=str, location='form')
method_put.add_argument('date_of_decision_on_state_registration_of_changes', type=str, location='form')
method_put.add_argument('date_of_decision_to_terminate_the_application', type=str, location='form')
# method_put.add_argument('doc_copy_of_method', type=reqparse.FileStorage, location='files')
# method_put.add_argument('doc_report_review', type=reqparse.FileStorage, location='files')
# method_put.add_argument('doc_certificate_of_approbation', type=reqparse.FileStorage, location='files')
# method_put.add_argument('doc_copy_of_implementation', type=reqparse.FileStorage, location='files')
# method_put.add_argument('doc_discount_card', type=reqparse.FileStorage, location='files')
method_put.add_argument('author', type=str, location='form', help="Second name and initials of method author")


auth_fields = app_api.model('Auth', {'email': fields.String(required=True), 'password': fields.String(required=True)})

user_fields = app_api.model('User', {'email': fields.String(required=True), 'full_name': fields.String(required=True),
                                     'date_of_birth': fields.Date(required=True),
                                     'series_passport': fields.String(required=True),
                                     'passport_number': fields.String(required=True),
                                     'date_of_issue_of_passport': fields.Date(required=True),
                                     'id_authority_that_issued_the_passport': fields.Integer(required=True),
                                     'ITN': fields.String(required=True),
                                     'id_organizations': fields.Integer(required=True),
                                     'id_position': fields.Integer(required=True),
                                     'region': fields.String(required=True), 'city': fields.String(required=True),
                                     'street': fields.String(required=True),
                                     'house_number': fields.String(required=True),
                                     'flat_number': fields.Integer(required=False)
                                     })
id_user_fields = app_api.model('Email', {'id_user':  fields.Integer(required=True)})