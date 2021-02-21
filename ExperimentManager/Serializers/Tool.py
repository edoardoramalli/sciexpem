def drop_fields(obj, fields):
    fields = 'id' if fields is None else fields

    if fields is not None:
        # Drop any fields that are not specified in the `fields` argument.
        allowed = set(fields) if isinstance(fields, tuple) else {fields}
        existing = set(obj.fields)
        for field_name in existing - allowed:
            obj.fields.pop(field_name)
