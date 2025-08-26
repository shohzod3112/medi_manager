class ReadWriteRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == "myapp":
            return "replica"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "myapp":
            return "default"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db == obj2._state.db:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "myapp":
            return db == "default"
        return None
