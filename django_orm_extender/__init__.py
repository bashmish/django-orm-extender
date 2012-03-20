from itertools import groupby

from django.contrib.contenttypes.models import ContentType



def attach_m2m_lists(qs, to_related_name, fields_names=[]):
    """Attach M2M relation data to QuerySet objects with a single query.

    :param qs: QuerySet for model in M2M relation.
    :type qs: QuerySet
    :param to_related_name: M2M relation name.
    :type to_related_name: str
    :param fields_names: If explicit intermediary model is used then you can enumerate required fields names here.
    :type fields_names: list of str

    .. note::
       If fields_names is empty then list will be a plain sequence of related model objects.
       Otherwise list will contain objects with attributes for every required field.
    """

    # M2M field
    to_related_field = qs.model._meta.get_field(to_related_name)

    # intermediary M2M model
    m2m_model = to_related_field.rel.through

    # ForeignKey fields names
    from_field_name = to_related_field.m2m_field_name()
    to_field_name = to_related_field.m2m_reverse_field_name()

    # filter hack
    filter_kwargs = {'%s__id__in' % from_field_name: qs}

    if fields_names:

        # list of fields to order M2M query
        order_by_fields = [from_field_name]
        order_by_fields.extend(fields_names)

        # M2M QuerySet
        m2m_qs = m2m_model.objects.select_related().filter(**filter_kwargs).order_by(*order_by_fields)

        # mapping dict with id as a key
        from_id_map = dict(
            # regroup M2M QuerySet by id
            [(from_id, [obj for obj in m2m_qs])
             for from_id, m2m_qs in groupby(m2m_qs, lambda obj: getattr(obj, from_field_name).id)]
        )

    else:

        # M2M QuerySet
        m2m_qs = m2m_model.objects.select_related().filter(**filter_kwargs).order_by(from_field_name)

        # mapping dict with id as a key
        from_id_map = dict(
            # regroup M2M QuerySet by id and get to_field object
            [(from_id, [getattr(obj, to_field_name) for obj in m2m_qs])
             for from_id, m2m_qs in groupby(m2m_qs, lambda obj: getattr(obj, from_field_name).id)]
        )

    # unique name for generated M2M lists
    # (original name is used for ManyToManyRelManager and can't be reassigned)
    cache_name = '%s_list' % to_related_name

    # attach lists to corresponding QuerySet objects
    for obj in qs:
        setattr(obj, cache_name, from_id_map.get(obj.id, []))



def attach_generic_lists(qs, to_related_name):
    """Attach generic relation data to QuerySet objects with a single query.

    :param qs: QuerySet for model in generic relation.
    :type qs: QuerySet
    :param to_related_name: Generic relation name.
    :type to_related_name: str
    """

    # generic relation field
    to_related_field = qs.model._meta.get_field(to_related_name)

    # generic model
    generic_model = to_related_field.rel.to

    # generic QuerySet
    generic_qs = generic_model.objects.filter(
        content_type=ContentType.objects.get_for_model(qs.model),
        object_id__in=qs
    ).order_by('object_id')

    # mapping dict with id as a key
    from_id_map = dict(
        [(from_id, list(generic_qs)) for from_id, generic_qs in groupby(generic_qs, lambda obj: obj.object_id)]
    )

    # unique name for generated generic lists
    # (original name is used for GenericRelation and can't be reassigned)
    cache_name = '%s_list' % to_related_name

    # attach lists to corresponding QuerySet objects
    for obj in qs:
        setattr(obj, cache_name, from_id_map.get(obj.id, []))



def select_related_generic(queryset, select_related=None, ct_field='content_type', fk_field='object_pk', co_field='content_object'):
    """Extended select_related for generic relations.

    .. note::
       Based on http://blog.roseman.org.uk/2010/02/22/django-patterns-part-4-forwards-generic-relations/
    """
    if select_related:
        select_related = [ct_field] + list(select_related)
    else:
        select_related = [ct_field]
    queryset = queryset.select_related(*select_related)

    generics = {}
    content_types = {}
    for item in queryset:
        ct_id = getattr(item, '%s_id' % ct_field)
        generics.setdefault(ct_id, set()).add(int(getattr(item, fk_field)))
        content_types.setdefault(ct_id, getattr(item, ct_field))

    relations = {}
    for ct_id, fk_set in generics.items():
        ct_model = content_types[ct_id].model_class()
        relations[ct_id] = ct_model.objects.in_bulk(list(fk_set))

    for item in queryset:
        try:
            setattr(item, '_%s_cache' % co_field, relations[getattr(item, '%s_id' % ct_field)][int(getattr(item, fk_field))])
        except KeyError:
            pass

    return queryset
