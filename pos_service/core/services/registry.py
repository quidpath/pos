from datetime import datetime
from typing import Any, Dict, Optional, Type, Union

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q, QuerySet

from pos_service.core.services.service_base import ServiceBase


class ServiceRegistry:
    """Registry to handle CRUD operations for different models."""

    def get_model_class(self, model_name: str) -> Type[models.Model]:
        content_type = ContentType.objects.filter(model=model_name.lower()).first()
        if content_type:
            return content_type.model_class()
        raise ValueError(f"Model '{model_name}' is not recognized.")

    def get_service(self, model: Type[models.Model]) -> ServiceBase:
        return ServiceBase(manager=model.objects)

    def serialize_data(self, data: Any) -> Any:
        if isinstance(data, models.Model):
            return self.serialize_instance(data)
        elif isinstance(data, QuerySet):
            return [self.serialize_instance(instance) for instance in data]
        return data

    def serialize_instance(self, instance: models.Model) -> dict:
        data = {}
        for field in instance._meta.fields:
            value = getattr(instance, field.name)
            if isinstance(value, datetime):
                data[field.name] = value.isoformat()
            else:
                data[field.name] = value
        return data

    def database(
        self,
        model_name: str,
        operation: str,
        instance_id: Optional[Any] = None,
        data: Optional[Union[Dict[str, Any], Q]] = None,
        soft: bool = True,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        model_class = self.get_model_class(model_name)
        service = self.get_service(model_class)
        if data is None:
            data = {}
        if operation == "create":
            return self.serialize_data(service.create(**data))
        elif operation == "get":
            if not data:
                raise ValueError("Filter criteria must be provided for 'get' operation.")
            return self.serialize_data(service.get(**data))
        elif operation == "update":
            if instance_id is None:
                raise ValueError("Instance ID is required for 'update' operation.")
            return self.serialize_data(service.update(instance_id, **data))
        elif operation == "delete":
            if instance_id is None:
                raise ValueError("Instance ID is required for 'delete' operation.")
            return service.delete(instance_id, soft=soft)
        elif operation == "filter":
            query = Q()
            if isinstance(data, Q):
                query &= data
            elif isinstance(data, dict):
                query &= Q(**data)
            else:
                raise ValueError("Data for 'filter' operation must be a Q object or dictionary.")
            if additional_filters:
                query &= Q(**additional_filters)
            return self.serialize_data(service.manager.filter(query))
        elif operation == "all":
            return self.serialize_data(service.get_all_records())
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    def build_queries(
        self,
        model_name: str,
        query: Q,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        return self.database(model_name, "filter", data=query, additional_filters=additional_filters)
