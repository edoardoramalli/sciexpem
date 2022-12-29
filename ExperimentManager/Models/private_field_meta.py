from django.db import models


class PrivateFieldsMeta(models.base.ModelBase):
    """
    Meta class that looks at **private_fields** attribute in Model Meta Option
    and renames the class attribute to **_{attribute}**, but keeps db column name original.
    This allows to encapsulate field's data.
    # Short example here.
    # >>> class Employee(models.Model, metaclass=PrivateFieldsMeta):
    # >>>     name = models.CharField(max_length=256)
    # >>>     rate = models.FloatField(default=0)
    # >>>     class Meta:
    # >>>         private_fields = ('rate', )
    """
    def __new__(cls, name, bases, attrs):
        attr_meta = attrs.get('Meta', None)

        if hasattr(attr_meta, 'private_fields'):
            cls._rename_private_fields(attrs, attr_meta.private_fields)

            # cleanup private_fields meta attribute
            del attr_meta.private_fields

        result = super(PrivateFieldsMeta, cls).__new__(cls, name, bases, attrs)
        return result

    @classmethod
    def _rename_private_fields(cls, attrs, private_fields):
        """
        Method that renames all fields listed in private_fields to **_{field}**.
        It has side effect of changing attrs: pop original private field and put new one.
        """
        for field_name in private_fields:
            field = attrs.pop(field_name, None)
            if isinstance(field, models.Field):
                field.db_column = field.db_column or field_name
                private_field_name = '_%s' % field_name
                attrs[private_field_name] = field