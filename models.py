from __main__ import db
from sqlalchemy import BigInteger, Date,String
from sqlalchemy.ext.declarative import DeclarativeMeta
import json
import datetime
from sqlalchemy.orm import validates

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    full_name = db.Column(db.Text, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    series_passport = db.Column(String(2), nullable=True)
    passport_number = db.Column(String(9), nullable=False)
    date_of_issue_of_passport = db.Column(db.Date, nullable=False)
    id_authority_that_issued_the_passport = db.Column(db.Integer, db.ForeignKey('authorityIssuedPassport.id'),
                                                      nullable=False)
    authority=db.relationship('AuthorityIssuedPassport', backref=db.backref('users', lazy=True))
    ITN = db.Column(String(10), nullable=False)
    password = db.Column(db.Text, nullable=False)
    id_role = db.Column(db.Integer, db.ForeignKey('userRole.id'), nullable=False)
    role=db.relationship('UserRole',backref=db.backref('users', lazy=True))
    id_organizations = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    organization = db.relationship('Organization', backref=db.backref('users', lazy=True))
    id_position = db.Column(db.Integer, db.ForeignKey('userPosition.id'), nullable=False)
    position = db.relationship('UserPosition', backref=db.backref('users', lazy=True))
    id_adress = db.Column(db.Integer, db.ForeignKey('adresses.id'), nullable=False)
    is_activate=db.Column(db.Boolean, nullable=False )
    logs = db.relationship('Logs', backref='users', lazy=True)

    @validates('email')
    def _validate_email(self,key,email):
        if not email:
            raise AssertionError('No email provided!')
        if Users.query.filter(Users.email == email).first():
            raise AssertionError('Email is already in use!')
        return email
    @validates('passport_number')
    def _validate_passport_number(self,key,passport_number):
        if not passport_number:
            raise AssertionError('No passport number provided!')
        if Users.query.filter(Users.passport_number == passport_number).first():
            raise AssertionError('Passport number is already in use!')
        return passport_number
    @validates('ITN')
    def _validate_ITN(self,key,ITN):
        if not ITN:
            raise AssertionError('No ITN provided!')
        if Users.query.filter(Users.ITN == ITN).first():
            raise AssertionError('ITN is already in use!')
        return ITN

    def __repr__(self):
        return f'<User id:{self.id}, full_name:{self.full_name}, email:{self.email}>'


class Adress(db.Model):
    __tablename__ = 'adresses'
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.Text, nullable=False)
    city = db.Column(db.Text, nullable=False)
    street = db.Column(db.Text, nullable=False)
    house_number =  db.Column(String(10), nullable=False)
    flat_number = db.Column(db.Integer, nullable=True)
    authorities=db.relationship('AuthorityIssuedPassport', backref='adresses', lazy=True)
    users = db.relationship('Users', backref='adresses', lazy=True)
    def __repr__(self):
        return f'<Address id:{self.id}, region:{self.region}, city:{self.city},street:{self.street}, ' \
               f'house_number:{self.house_number},flat_number:{self.flat_number}>'


class AuthorityIssuedPassport(db.Model):
    __tablename__ = 'authorityIssuedPassport'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer, nullable=False)
    name = db.Column(db.Text, nullable=False)
    id_adress = db.Column(db.Integer, db.ForeignKey('adresses.id'), nullable=False)

    def __repr__(self):
        return f'<AuthorityIssuedPassport id:{self.id}, code:{self.code}, name:{self.name},id_adress:{self.id_adress}>'


class DomainsOfMethod(db.Model):
    __tablename__ = 'domainsOfMethod'
    id = db.Column(db.Integer, primary_key=True)
    id_types = db.Column(db.Integer, db.ForeignKey('typesOfMethods.id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    methods = db.relationship('Methods', backref='domainsOfMethod', lazy=True)

    def __repr__(self):
        return f'<DomainsOfMethod id:{self.id}, id_types:{self.id_types}, name:{self.name}>'



class TypesOfMethods(db.Model):
    __tablename__ = 'typesOfMethods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    domains = db.relationship('DomainsOfMethod', backref='typesOfMethods', lazy=True)

    def __repr__(self):
        return f'<TypesOfMethod id:{self.id}, name:{self.name}>'


class Logs(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id',ondelete='SET NULL'), nullable=True)
    id_method =db.Column(db.Integer, db.ForeignKey('methods.id',ondelete='SET NULL'),nullable=True)
    id_type = db.Column(db.Integer, db.ForeignKey('typeAction.id'), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    id_old_value = db.Column(db.Integer, db.ForeignKey('methodslogs.id'), nullable=False)
    method = db.relationship('Methods', backref=db.backref('logs', lazy=True))


class Methods(db.Model):
    __tablename__ = 'methods'
    id = db.Column(db.Integer, primary_key=True)
    registration_code = db.Column(db.Text, nullable=False, unique=True)
    id_domains = db.Column(db.Integer, db.ForeignKey('domainsOfMethod.id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    year_creation = db.Column(db.Integer, nullable=False)
    year_making_changes = db.Column(db.Integer, nullable=True)
    year_termination_application = db.Column(db.Integer, nullable=True)
    date_of_decision_on_state_registration = db.Column(Date, nullable=False)
    date_of_decision_on_state_registration_of_changes = db.Column(Date, nullable=True)
    date_of_decision_to_terminate_the_application = db.Column(Date, nullable=True)
    doc_copy_of_method = db.Column(db.Text, nullable=False)
    doc_report_review = db.Column(db.Text, nullable=False)
    doc_certificate_of_approbation = db.Column(db.Text, nullable=False)
    doc_copy_of_implementation = db.Column(db.Text, nullable=False)
    doc_discount_card = db.Column(db.Text, nullable=False)
    author = db.Column(db.Text, nullable=False)

    @validates('registration_code')
    def _validate_registration_code(self, key, registration_code):
        if Methods.query.filter(Methods.registration_code == registration_code).first():
            raise AssertionError('Registration_code is already in use!')
        return registration_code

    def __repr__(self):
        return f'<Methods id:{self.id},  name:{self.name}, author:{self.author}>'





class MethodsLogs(db.Model):
    __tablename__ = 'methodslogs'
    id = db.Column(db.Integer, primary_key=True)
    registration_code = db.Column(db.Text, nullable=False)
    id_domains = db.Column(db.Integer, db.ForeignKey('domainsOfMethod.id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    year_creation = db.Column(db.Integer, nullable=False)
    year_making_changes = db.Column(db.Integer, nullable=True)
    year_termination_application = db.Column(db.Integer, nullable=True)
    date_of_decision_on_state_registration = db.Column(Date, nullable=False)
    date_of_decision_on_state_registration_of_changes = db.Column(Date, nullable=True)
    date_of_decision_to_terminate_the_application = db.Column(Date, nullable=True)
    doc_copy_of_method = db.Column(db.Text, nullable=False)
    doc_report_review = db.Column(db.Text, nullable=False)
    doc_certificate_of_approbation = db.Column(db.Text, nullable=False)
    doc_copy_of_implementation = db.Column(db.Text, nullable=False)
    doc_discount_card = db.Column(db.Text, nullable=False)
    author = db.Column(db.Text, nullable=False)
    logs = db.relationship('Logs', backref='methodslogs', lazy=True)

    def __repr__(self):
        return f'<MethodsLogs id:{self.id},  name:{self.name}, author:{self.author}>'

class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    def __repr__(self):
        return f'<Organizations id:{self.id}, name:{self.name}>'


class TypeAction(db.Model):
    __tablename__ = 'typeAction'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    logs = db.relationship('Logs', backref='typeAction', lazy=True)
    def __repr__(self):
        return f'<TypeAction id:{self.id}, name:{self.name}>'


class UserPosition(db.Model):
    __tablename__ = 'userPosition'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    def __repr__(self):
        return f'<UserPosition id:{self.id}, name:{self.name}>'


class UserRole(db.Model):
    __tablename__ = 'userRole'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    def __repr__(self):
        return f'<UserRole id:{self.id}, name:{self.name}>'


def new_alchemy_encoder(revisit_self = False, fields_to_expand = []):
    _visited_objs = []

    class AlchemyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj.__class__, DeclarativeMeta):
                # don't re-visit self
                if revisit_self:
                    if (obj in _visited_objs )and (obj.__class__ is not DomainsOfMethod):
                        return None
                    _visited_objs.append(obj)

                # go through each field in this SQLalchemy class
                fields = {}
                for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                    val = obj.__getattribute__(field)
                    if field =='password':
                        # fields[field] = None
                        continue
                    # is this field another SQLalchemy object, or a list of SQLalchemy objects?
                    if isinstance(val, datetime.date):
                        val= val.__str__()
                    elif isinstance(val.__class__, DeclarativeMeta) or (isinstance(val, list) and len(val) > 0 and isinstance(val[0].__class__, DeclarativeMeta)):
                        # unless we're expanding this field, stop here
                        if field not in fields_to_expand:
                            continue
                        else:
                            fields[field] = val
                            continue
                    if not isinstance(val,list):
                        fields[field] = val
                # a json-encodable dict
                del fields["query"],fields["query_class"],fields["registry"]
                # print("FIELDS")
                # print(fields)
                return fields

            return json.JSONEncoder.default(self, obj)

    return AlchemyEncoder
