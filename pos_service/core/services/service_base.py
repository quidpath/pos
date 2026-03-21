from typing import Any, Optional

from django.db.models import Model, QuerySet


class ServiceBase:
    def __init__(self, manager: QuerySet):
        self.manager = manager

    def create(self, **kwargs) -> Model:
        return self.manager.create(**kwargs)

    def get(self, **kwargs) -> Optional[Model]:
        return self.manager.filter(**kwargs).first()

    def update(self, instance_id: Any, **kwargs) -> Optional[Model]:
        instance = self.manager.filter(pk=instance_id).first()
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            instance.save()
            return instance
        return None

    def delete(self, instance_id: Any, soft: bool = True) -> bool:
        instance = self.manager.filter(pk=instance_id).first()
        if instance:
            if soft and hasattr(instance, "is_active"):
                instance.is_active = False
                instance.save()
            else:
                instance.delete()
            return True
        return False

    def get_all_records(self) -> QuerySet:
        return self.manager.all()
