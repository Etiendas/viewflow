from django.db import models


def get_model_display_data(root_instance):
    """
    Returns structure with model fields and related from same app
    [(Title, [(Field Title, Value), ... ]), ...]
    """
    result = []
    new_objects = [(root_instance._meta.verbose_name.title(), root_instance)]

    processed_models, processed_objects = [], []

    def expand_required(instance):
        if instance in processed_objects:
            return False
        if instance.__class__ in processed_models:
            return False
        return root_instance._meta.app_label == instance._meta.app_label

    while new_objects:
        root_title, root = new_objects.pop(0)
        children = []

        processed_objects.append(root)
        processed_models.append(root.__class__)

        # objects fields
        for field in root._meta.fields:
            if isinstance(field, models.AutoField):
                continue
            elif isinstance(field, models.ForeignKey) and not field.auto_created:
                related_id = getattr(root, field.get_attname())
                if related_id is not None:
                    related = getattr(root, field.name)
                    if expand_required(related):
                        new_objects.append((field.verbose_name.title(), related))
                    else:
                        children.append((field.verbose_name.title(), related))
            else:
                choice_display_attr = "get_{}_display".format(field.get_attname())
                if hasattr(root, choice_display_attr):
                    value = getattr(root, choice_display_attr)()
                else:
                    value = getattr(root, field.get_attname())

                if value is not None:
                    children.append((field.verbose_name.title(), value))

        # backward relations
        for relation in root._meta.get_all_related_objects():
            if not isinstance(relation.field, models.OneToOneField):
                for related in getattr(root, relation.get_accessor_name()).all():
                    if expand_required(related):
                        new_objects.append((related._meta.verbose_name.title(), related))

        # if any suitable for display children found
        if children:
            result.append((root_title, children))

    return result
