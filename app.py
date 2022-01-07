import datetime
from datetime import timezone
import cloudinary
from cloudinary import uploader
from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource
from functools import wraps
from hashlib import sha256
import jwt
import json
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError
import secrets
import string
from celery_worker import send_confirmation_email
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

app = Flask(__name__)
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}
UPLOAD_FOLDER = '/files'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app_api = Api(app, authorizations=authorizations, security='apikey')

cloudinary.config(
    cloud_name=os.environ['CLOUDINARY_CLOUD_NAME'],
    api_key=os.environ['CLOUDINARY_API_KEY'],
    api_secret=os.environ['CLOUDINARY_API_SECRET'],
    secure=True
)
name_space = app_api.namespace('main', description='Apis')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = os.environ['SQLALCHEMY_SECRET_KEY']
USER = None
db = SQLAlchemy(app)
from database import DB
from models import new_alchemy_encoder
from myfields import auth_fields, parser, method_put, user_fields, id_user_fields

data_base = DB(db)


@app.after_request
def apply_caching(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


def generate_password():
    secretsGenerator = secrets.SystemRandom()
    random_number = secretsGenerator.randint(8, 15)
    stringSource = string.ascii_letters + string.digits
    password = ''
    for i in range(random_number):
        password += secrets.choice(stringSource)
    return password


def roles_required(roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'Authorization' in request.headers:
                try:
                    auth_header = jwt.decode(request.headers.get('Authorization').split()[1], app.config['SECRET_KEY'],
                                             algorithms=["HS256"])
                    global USER
                    USER = auth_header
                    role = "Admin" if auth_header['role'] == 2 else "Registrar"
                    if role in roles:
                        return func(*args, **kwargs)
                    else:
                        return Response(json.dumps({"error": "You don`t have rights for that!"}), mimetype='text/json',
                                        status=403)
                except ExpiredSignatureError as error:
                    return Response(json.dumps({"error": str(error)}), mimetype='text/json', status=401)
                except InvalidSignatureError as error:
                    return Response(json.dumps({"error": str(error)}), mimetype='text/json', status=400)

            elif 'User' in roles:
                return func(*args, **kwargs)
            return Response(json.dumps({"error": "Need Authorization"}), mimetype='text/json', status=401)

        return wrapper

    return decorator


@name_space.route("/login")
class Login(Resource):
    @app_api.expect(auth_fields)
    def post(self):
        data = request.json
        if ('email' in data.keys()) and ('password' in data.keys()):
            email = data['email']
            password = sha256(data['password'].encode('utf-8')).hexdigest()
            user = data_base.get_user(email, password)
            if user:
                if not user.is_activate:
                    return Response(json.dumps({"error": "User is deactivated"}), mimetype='text/json', status=403)
                res = Response(json.dumps({'Token': jwt.encode({"id": user.id, "role": user.id_role,
                                                                "exp": datetime.datetime.now(
                                                                    tz=timezone.utc) + datetime.timedelta(
                                                                    minutes=55)}, app.config.get("SECRET_KEY"),
                                                               algorithm="HS256")}), mimetype='text/json')
                return res
            else:
                return Response(json.dumps({"error": "Email or password are incorrect"}), mimetype='text/json',
                                status=404)

        else:
            return Response(json.dumps({"error": "Missed arguments"}), mimetype='text/json', status=400)


@name_space.route("/token")
class Token(Resource):
    def get(self):
        if 'Authorization' in request.headers:
            try:
                auth_header = jwt.decode(request.headers.get('Authorization').split()[1], app.config['SECRET_KEY'],
                                         algorithms=["HS256"], options={'verify_exp': False})
                user = data_base.get_user_id(auth_header["id"])
                if not user.is_activate:
                    return Response(json.dumps({"error": "User is deactivated"}), mimetype='text/json', status=403)
                global USER
                USER = auth_header
                return Response(json.dumps({"Token": jwt.encode({"id": auth_header['id'], "role": auth_header['role'],
                                                                 "exp": datetime.datetime.now(
                                                                     tz=timezone.utc) + datetime.timedelta(
                                                                     minutes=15)}, app.config.get("SECRET_KEY"),
                                                                algorithm="HS256")}), mimetype='text/json', )
            except ExpiredSignatureError as error:
                return Response(json.dumps({"error": str(error)}), mimetype='text/json', status=400)
        return Response(json.dumps({"error": "Need Authorization"}), mimetype='text/json', status=401)


@name_space.route("/method")
class Methods(Resource):
    @app_api.doc(params={'ids': 'ids', 'name': 'name', 'code': 'Регистрационный код', 'page': "Page for pagination",
                         'count': "Number methods on one page"})
    @roles_required({"Registrar", "User", "Admin"})
    def get(self):
        count = 10
        page = 1
        if request.args.get("count"):
            count = int(request.args.get("count"))
        if request.args.get("page"):
            page = int(request.args.get("page"))
        results = data_base.get_all_methods(ids=request.args.get("ids"), name=request.args.get("name"),
                                            code=request.args.get("code"), page=page, count=count)
        js = json.dumps(results, cls=new_alchemy_encoder(False, ['domainsOfMethod', 'typesOfMethods']),
                        check_circular=False, ensure_ascii=False)
        if not USER:
            datas = json.loads(js)
            for data in datas["methods"]:
                del data["doc_copy_of_method"]
                del data["doc_report_review"]
                del data["doc_certificate_of_approbation"]
                del data["doc_copy_of_implementation"]
                del data["doc_discount_card"]
            js = json.dumps(datas, ensure_ascii=False)
        return Response(js, mimetype='text/json')

    @app_api.expect(parser)
    @roles_required({"Registrar"})
    def post(self):
        method = dict(request.form)
        method['year_creation'] = int(method['year_creation'])
        if 'year_making_changes' in method:
            method['year_making_changes'] = int(method['year_making_changes'])
        if 'year_termination_application' in method:
            method['year_termination_application'] = int(method['year_termination_application'])
        method['doc_copy_of_method'] = uploader.upload(request.files['doc_copy_of_method'])['url']

        method['doc_report_review'] = uploader.upload(request.files['doc_report_review'])['url']
        method['doc_certificate_of_approbation'] = uploader.upload(request.files['doc_certificate_of_approbation'])[
            'url']
        method['doc_copy_of_implementation'] = uploader.upload(request.files['doc_copy_of_implementation'])['url']
        method['doc_discount_card'] = uploader.upload(request.files['doc_discount_card'])['url']
        res = data_base.add_method(method, USER['id'])
        if isinstance(res, int):
            return Response(json.dumps({'id': res}), mimetype='text/json')
        return Response(json.dumps(res), mimetype='text/json', status=400)


@name_space.route("/method/<int:id>")
class Method(Resource):
    @roles_required({"Registrar", "User", "Admin"})
    def get(self, id):
        results = data_base.get_method(id)
        if isinstance(results, dict):
            js = json.dumps(results, ensure_ascii=False)
            return Response(js, mimetype='text/json', status=400)
        if not results:
            return Response(json.dumps({"error": "Method doesn't exist"}), mimetype='text/json', status=404)
        js = json.dumps(results, cls=new_alchemy_encoder(False, ['domainsOfMethod', 'typesOfMethods']),
                        check_circular=False, ensure_ascii=False)
        if not USER:
            data = json.loads(js)
            del data["doc_copy_of_method"]
            del data["doc_report_review"]
            del data["doc_certificate_of_approbation"]
            del data["doc_copy_of_implementation"]
            del data["doc_discount_card"]
            js = json.dumps(data, ensure_ascii=False)
        return Response(js, mimetype='text/json')

    @app_api.expect(method_put)
    @roles_required({"Registrar"})
    def put(self, id):
        method = dict(request.form)
        # print(method)
        method["id"] = id
        # if 'doc_copy_of_method' in request.files:
        #     method['doc_copy_of_method'] = uploader.upload(request.files['doc_copy_of_method'])['url']
        # if 'doc_report_review' in request.files:
        #     method['doc_report_review'] = uploader.upload(request.files['doc_report_review'])['url']
        # if 'doc_certificate_of_approbation' in request.files:
        #     method['doc_certificate_of_approbation'] = uploader.upload(request.files['doc_certificate_of_approbation'])[
        #         'url']
        # if 'doc_copy_of_implementation' in request.files:
        #     method['doc_copy_of_implementation'] = uploader.upload(request.files['doc_copy_of_implementation'])['url']
        # if 'doc_discount_card' in request.files:
        #     method['doc_discount_card'] = uploader.upload(request.files['doc_discount_card'])['url']
        if 'year_creation' in method:
            method['year_creation'] = int(method['year_creation'])
        if 'year_making_changes' in method:
            if method['year_making_changes'] is not None:
                method['year_making_changes'] = int(method['year_making_changes'])
        if 'year_termination_application' in method:
            if method['year_termination_application'] is not None:
                method['year_termination_application'] = int(method['year_termination_application'])
        print(method)
        res = data_base.update_method(method, USER['id'])
        if isinstance(res, int):
            return Response(json.dumps({'id': res}), mimetype='text/json')
        return Response(json.dumps(res), mimetype='text/json', status=400)


@name_space.route("/method/type")
class MethodTypes(Resource):
    def get(self):
        results = data_base.get_all_types_methods()
        js = json.dumps(results, cls=new_alchemy_encoder(False, ['domains']),
                        check_circular=False, ensure_ascii=False)
        return Response(js, mimetype='text/json')


@name_space.route("/method/type/<int:id>")
class MethodType(Resource):
    def get(self, id):
        results = data_base.get_type_methods(id)
        if isinstance(results, dict):
            js = json.dumps(results, ensure_ascii=False)
            return Response(js, mimetype='text/json', status=400)
        if not results:
            return Response(json.dumps({"error": "Type doesn't exist"}), mimetype='text/json', status=404)
        js = json.dumps(results, cls=new_alchemy_encoder(False, ['domains']),
                        check_circular=False, ensure_ascii=False)
        return Response(js, mimetype='text/json')


@name_space.route("/user/position")
class UserPositions(Resource):
    def get(self):
        results = data_base.get_all_user_positions()
        js = json.dumps(results, cls=new_alchemy_encoder(False),
                        check_circular=False, ensure_ascii=False)
        return Response(js, mimetype='text/json')


@name_space.route("/organization")
class Organizations(Resource):
    def get(self):
        results = data_base.get_all_organizations()
        js = json.dumps(results, cls=new_alchemy_encoder(False),
                        check_circular=False, ensure_ascii=False)
        return Response(js, mimetype='text/json')


@name_space.route("/addresses")
class Addresses(Resource):
    def get(self):
        results = data_base.get_all_adresses()
        js = json.dumps(results, cls=new_alchemy_encoder(False),
                        check_circular=False, ensure_ascii=False)
        return Response(js, mimetype='text/json')


@name_space.route("/authorities")
class Authorities(Resource):
    def get(self):
        results = data_base.get_all_authorities()
        js = json.dumps(results, cls=new_alchemy_encoder(False),
                        check_circular=False, ensure_ascii=False)
        return Response(js, mimetype='text/json')


@name_space.route("/actions")
class TypeAction(Resource):
    def get(self):
        results = data_base.get_all_typeAction()
        js = json.dumps(results, cls=new_alchemy_encoder(False),
                        check_circular=False, ensure_ascii=False)
        return Response(js, mimetype='text/json')


@name_space.route("/log")
class Logs(Resource):
    @app_api.doc(
        params={'full_name': 'Полное имя регистртора', 'email': 'Почта регистартора', 'code': 'Регистрационный код',
                'date1': 'Начало даты', 'date2': "Конец даты", 'id_typeAction': 'Тип операции',
                'page': "Page for pagination", 'count': "Number methods on one page"})
    @roles_required({"Admin"})
    def get(self):

        count = 10
        page = 1
        if request.args.get("count"):
            count = int(request.args.get("count"))
        if request.args.get("page"):
            page = int(request.args.get("page"))
        results = data_base.get_all_logs(full_name=request.args.get('full_name'), email=request.args.get('email'),
                                         code=request.args.get('code'), date1=request.args.get('date1'),
                                         date2=request.args.get('date2'),
                                         id_typeAction=request.args.get('id_typeAction'), page=page, count=count)
        print(results)
        js = json.dumps(results, cls=new_alchemy_encoder(False, ['methodslogs', 'users', 'typeAction','method']),
                        check_circular=False, ensure_ascii=False)
        print(js)
        return Response(js, mimetype='text/json')


@name_space.route("/log/<int:id>")
class Log(Resource):
    @app_api.doc(description="Return previous state")
    @roles_required({"Admin"})
    def delete(self, id):
        res = data_base.return_log(id)
        if isinstance(res, int):
            return Response(json.dumps({'id_method': res}), mimetype='text/json')
        return Response(json.dumps(res), mimetype='text/json', status=400)


@name_space.route("/user/info")
class User(Resource):
    @roles_required({"Admin", "Registrar"})
    def get(self):
        results = data_base.get_user_id(USER["id"])
        if isinstance(results, dict):
            js = json.dumps(results, ensure_ascii=False)
            return Response(js, mimetype='text/json', status=400)
        if not results:
            return Response(json.dumps({"error": "User doesn't exist"}), mimetype='text/json', status=404)
        js = json.dumps(results, cls=new_alchemy_encoder(False, ['domainsOfMethod', 'typesOfMethods']),
                        check_circular=False, ensure_ascii=False)
        return Response(js, mimetype='text/json')


@name_space.route("/user")
class Users(Resource):
    @roles_required({"Admin"})
    @app_api.expect(user_fields)
    def post(self):
        data = request.json
        password = generate_password()
        data['password'] = sha256(password.encode('utf-8')).hexdigest()
        data['id_role'] = 1
        data['is_activate']=True
        res = data_base.add_user(data)
        print(res)
        if isinstance(res, int):
            send_confirmation_email.delay(data['email'], password)
            return Response(json.dumps({'id_user': res}), mimetype='text/json')
        return Response(json.dumps(res), mimetype='text/json', status=400)

    @roles_required({"Admin"})
    @app_api.doc(params={'page': "Page for pagination", 'count': "Number methods on one page"})
    def get(self):
        count = 10
        page = 1
        if request.args.get("count"):
            count = int(request.args.get("count"))
        if request.args.get("page"):
            page = int(request.args.get("page"))
        results = data_base.get_all_users(page, count)
        js = json.dumps(results, cls=new_alchemy_encoder(False),
                        check_circular=False, ensure_ascii=False)
        return Response(js, mimetype='text/json')


@name_space.route("/user/<int:id>")
class User(Resource):

    @roles_required({"Admin"})
    def delete(self, id):
        res = data_base.delete_user(id)
        if isinstance(res, int):
            return Response(json.dumps({'id_user': res}), mimetype='text/json')
        return Response(json.dumps(res), mimetype='text/json', status=400)


@name_space.route("/user/activate/<int:id>")
class UserActivate(Resource):

    @roles_required({"Admin"})
    def put(self, id):
        res = data_base.activate_user(id)
        if isinstance(res, int):
            return Response(json.dumps({'id_user': res}), mimetype='text/json')
        return Response(json.dumps(res), mimetype='text/json', status=400)


@name_space.route("/user/deactivate/<int:id>")
class UserDeactivate(Resource):

    @roles_required({"Admin"})
    def put(self, id):
        res = data_base.deactivate_user(id)
        if isinstance(res, int):
            return Response(json.dumps({'id_user': res}), mimetype='text/json')
        return Response(json.dumps(res), mimetype='text/json', status=400)


@name_space.route("/user/send")
class Email(Resource):
    @roles_required({"Admin"})
    @app_api.expect(id_user_fields)
    def post(self):
        data = request.json
        password = generate_password()
        res = data_base.update_user(data['id_user'], sha256(password.encode('utf-8')).hexdigest())
        if isinstance(res, str):
            send_confirmation_email.delay(res, password)
            return Response(json.dumps({'email': res}), mimetype='text/json')
        return Response(json.dumps(res), mimetype='text/json', status=400)


if __name__ == '__main__':
    app.run(debug=True)
