def drop_fields(obj, fields):


    if fields is None:
        fields = 'id'
    elif fields is not None and 'id' not in fields:
        fields = fields + tuple(['id'])

    if fields is not None:
        # Drop any fields that are not specified in the `fields` argument.
        allowed = set(fields) if isinstance(fields, tuple) else {fields}
        existing = set(obj.fields)
        for field_name in existing - allowed:
            obj.fields.pop(field_name)
    # print("EDOOOOO", obj.__class__.__name__)
    # print(obj.fields)
