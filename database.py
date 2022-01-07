from models import Methods, Logs, MethodsLogs, TypesOfMethods, UserPosition, Organization, Adress, \
    AuthorityIssuedPassport, TypeAction, Users
from sqlalchemy import exc, inspect
import datetime


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


class DB:
    def __init__(self, db):
        self.db = db

    def get_all_methods(self, name=None, ids=None, code=None,page=1,count=10):
        try:
            query = Methods.query
            if name:
                query = query.filter(Methods.name.like(f"%%{name}%%"))
            if code:
                query = query.filter(Methods.registration_code.like(f"%%{code}%%"))
            if ids:
                ids = ids.split(',')
                ids = [int(id) for id in ids]
                query = query.filter(Methods.id_domains.in_(ids))
            res={}
            pag=query.paginate(page,count,error_out=False)
            res["methods"]=pag.items
            res["count"] = pag.total
        except AssertionError as e:
            print(str(e))
            return {"error": str(e)}
        return res

    def add_method(self, method_data, user):
        try:
            method = Methods(**method_data)
            self.db.session.add(method)
            self.db.session.commit()
        except exc.SQLAlchemyError as e:
            return {"error": "Creation method is failed! Please, check up your fields."}
        except AssertionError as e:
            return {"error": str(e)}
        try:
            log = Logs(id_user=user, id_method=method.id, id_type=1, datetime=datetime.datetime.now())
            self.db.session.add(log)
            self.db.session.commit()
        except exc.SQLAlchemyError as e:
            self.db.session.delete(method)
            self.db.session.commit()
            return {"error": "Creation method is failed! Probably user was deleted."}
        return method.id


    def update_method(self, method_data, user):
        try:
            id = method_data.pop('id', None)
            method = Methods.query.get(id)
            method = object_as_dict(method)
            del method['id']
            meth=Methods.query.get(id)
            for key, value in method_data.items():
                setattr(meth, key, value)
            self.db.session.commit()
        except exc.SQLAlchemyError as e:
            return {"error": "Update method failed!"}
        except AssertionError as e:
            return {"error": str(e)}
        log_meth=None
        try:
            log_meth = MethodsLogs(**method)
            self.db.session.add(log_meth)
            self.db.session.commit()
            log = Logs(id_user=user, id_method=id, id_type=2, datetime=datetime.datetime.now(),
                       id_old_value=log_meth.id)
            self.db.session.add(log)
            self.db.session.commit()
        except exc.SQLAlchemyError as e:
            Methods.query.filter_by(id=id).update(**method)
            self.db.session.commit()
            self.db.session.delete(log_meth)
            self.db.session.commit()
            return {"error": "Update method failed! Please, check up your fields."}
        return id

    def get_method(self, id):
        try:
            method = Methods.query.get(id)
            return method
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def get_all_types_methods(self):
        try:
            return TypesOfMethods.query.all()
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def get_type_methods(self, id):
        try:
            return TypesOfMethods.query.get(id)
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def get_all_user_positions(self):
        try:
            return UserPosition.query.all()
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def get_all_organizations(self):
        try:
            return Organization.query.all()
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def get_all_adresses(self):
        try:
            return Adress.query.all()
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def get_all_authorities(self):
        try:
            return AuthorityIssuedPassport.query.all()
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def get_all_typeAction(self):
        try:
            return TypeAction.query.all()
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def get_all_logs(self, full_name, email, code, date1, date2, id_typeAction,page,count):
        try:
            query = Logs.query.join(Users).join(Methods,Methods.id==Logs.id_method)
            if full_name:
                query = query.filter(Users.full_name.like(f"%%{full_name}%%"))
            if email:
                query = query.filter(Users.email.like(f"%%{email}%%"))
            if code:
                query = query.filter(Methods.registration_code.like(f"%%{code}%%"))
            if id_typeAction:
                query = query.filter(Logs.id_type == id_typeAction)
            if date1:
                query = query.filter(Logs.datetime >= date1)
            if date2:
                query = query.filter(Logs.datetime <= date2)
            res = {}
            pag=query.paginate(page, count, error_out=False)
            res["logs"] = pag.items
            res["count"] = pag.total
            return res
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}
    def return_log(self, id):
        try:
            log = Logs.query.get(id)
            id_method=log.id_method
            meth = Methods.query.get(id_method)
            if log.id_type == 1 and meth:
                self.db.session.delete(meth)
                self.db.session.commit()
            elif log.id_type == 2 and meth:
                method = object_as_dict(meth)
                del method['id']
                method_log = MethodsLogs.query.get(log.id_old_value)
                method_log = object_as_dict(method_log)
                Methods.query.filter_by(id=log.id_method).update(method_log)
                self.db.session.commit()
            else:
                return {"error": 'It is already deleted'}
            return log.id_method
            # print(id,user_id)
            # log=Logs.query.get(id)
            # meth=Methods.query.get(log.id_method)
            # type=0
            # log_meth={}
            # if log.id_type!=1 and not meth:
            #     method_log = MethodsLogs.query.get(log.id_old_value)
            #     print(method_log)
            #     method_log = object_as_dict(method_log)
            #     method = Methods(**method_log)
            #     self.db.session.add(method)
            #     self.db.session.commit()
            #     log = Logs(id_user=user_id, id_method=log.id_method, id_type=1, datetime=datetime.datetime.now(), )
            #     self.db.session.add(log)
            #     self.db.session.commit()
            #     return log.id_method
            # if log.id_type==1 and meth:
            #     self.db.session.delete(meth)
            #     self.db.session.commit()
            #     type=3
            # elif log.id_type==1:
            #     return 0
            # elif meth:
            #     method = object_as_dict(meth)
            #     del method['id']
            #     log_meth = MethodsLogs(**method)
            #     self.db.session.add(log_meth)
            #     self.db.session.commit()
            #     method_log = MethodsLogs.query.get(log.id_old_value)
            #     print(method_log)
            #     method_log = object_as_dict(method_log)
            #     Methods.query.filter_by(id=log.id_method).update(method_log)
            #     self.db.session.commit()
            #     type=2
            # log = Logs(id_user=user_id, id_method=log.id_method, id_type=type, datetime=datetime.datetime.now(),
            #            id_old_value=log_meth.id)
            # self.db.session.add(log)
            # self.db.session.commit()
            # return log.id_method
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}
    def get_user(self,email,password):
        return Users.query.filter_by(email=email,
                                         password=password).first()
    def get_user_id(self,id):
        try:
            user = Users.query.get(id)
            return user
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}
    def add_user(self, user_adress):
        try:
            adress = {}
            adress['region'] = user_adress.pop('region')
            adress['city'] = user_adress.pop('city')
            adress['street'] = user_adress.pop('street')
            adress['house_number'] = user_adress.pop('house_number')
            adress['flat_number'] = user_adress.pop('flat_number', None)
            address = Adress(**adress)
            self.db.session.add(address)
            self.db.session.commit()
            user_adress["id_adress"] = address.id
            user = Users(**user_adress)
            self.db.session.add(user)
            self.db.session.commit()
            return user.id
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}
        except AssertionError as e:
            return {"error": str(e)}

    def update_user(self, id, password):
        try:
            Users.query.filter_by(id=id).update({'password':password})
            self.db.session.commit()
            user = Users.query.get(id)
            return user.email
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def delete_user(self, id):
        try:
            user = Users.query.get(id)
            if user.id_role==2:
                return {"error": "You can`t delete admin!"}
            self.db.session.delete(user)
            self.db.session.commit()
            return id
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def get_all_users(self,page,count):
        try:
            res = {}
            pag=Users.query.filter_by(id_role=1).paginate(page, count, error_out=False)
            res["users"] = pag.items
            res["count"] = pag.total
            return res
        except exc.SQLAlchemyError as e:
            return {"error": str(e)}

    def activate_user(self,id):
        user = Users.query.get(id)
        if not user:
            return {"error": "User doesn`t exist!"}
        if user.id_role==2:
            return {"error": "You can`t activate admin!"}
        if user.is_activate:
            return {"error": "It is already activated!"}
        user.is_activate=True
        self.db.session.commit()
        return id

    def deactivate_user(self, id):
        user = Users.query.get(id)
        if not user:
            return {"error": "User doesn`t exist!"}
        if user.id_role==2:
            return {"error": "You can`t deactivate admin!"}
        if not user.is_activate:
            return {"error": "It is already deactivated!"}
        user.is_activate=False
        self.db.session.commit()
        return id