# -*- coding: utf-8 -*-
from django.utils.translation import get_language
from django.db.models.query import EmptyQuerySet
from rest_framework_extensions.compat import force_text


class KeyBitBase(object):
    def __init__(self, params=None):
        self.params = params

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        """
        @rtype: dict
        """
        raise NotImplementedError()


class KeyBitDictBase(KeyBitBase):
    """Base class for dict-like source data processing.

    Look at HeadersKeyBit and QueryParamsKeyBit

    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        data = {}
        source_dict = self.get_source_dict(
            params=params,
            view_instance=view_instance,
            view_method=view_method,
            request=request,
            args=args,
            kwargs=kwargs
        )
        for key in params:
            value = source_dict.get(self.prepare_key_for_value_retrieving(key))
            if value is not None:
                data[self.prepare_key_for_value_assignment(key)] = force_text(value)
        return data

    def get_source_dict(self, params, view_instance, view_method, request, args, kwargs):
        raise NotImplementedError()

    def prepare_key_for_value_retrieving(self, key):
        return key

    def prepare_key_for_value_assignment(self, key):
        return key


class UniqueViewIdKeyBit(KeyBitBase):
    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        return u'.'.join([
            view_instance.__module__,
            view_instance.__class__.__name__
        ])


class UniqueMethodIdKeyBit(KeyBitBase):
    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        return u'.'.join([
            view_instance.__module__,
            view_instance.__class__.__name__,
            view_method.__name__
        ])


class LanguageKeyBit(KeyBitBase):
    """
    Return example:
        u'en'

    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        return force_text(get_language())


class FormatKeyBit(KeyBitBase):
    """
    Return example for json:
        u'json'

    Return example for html:
        u'html'
    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        return force_text(request.accepted_renderer.format)


class UserKeyBit(KeyBitBase):
    """
    Return example for anonymous:
        u'anonymous'

    Return example for authenticated (value is user id):
        u'10'
    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        if hasattr(request, 'user') and request.user and request.user.is_authenticated():
            return force_text(self._get_id_from_user(request.user))
        else:
            return u'anonymous'

    def _get_id_from_user(self, user):
        return user.id


class HeadersKeyBit(KeyBitDictBase):
    """
    Return example:
        {'accept-language': u'ru', 'x-geobase-id': '123'}

    """
    def get_source_dict(self, params, view_instance, view_method, request, args, kwargs):
        return request.META

    def prepare_key_for_value_retrieving(self, key):
        from rest_framework_extensions.utils import prepare_header_name

        return prepare_header_name(key.lower())  # Accept-Language => http_accept_language

    def prepare_key_for_value_assignment(self, key):
        return key.lower()  # Accept-Language => accept-language


class RequestMetaKeyBit(KeyBitDictBase):
    """
    Return example:
        {'REMOTE_ADDR': u'127.0.0.2', 'REMOTE_HOST': u'yandex.ru'}

    """

    def get_source_dict(self, params, view_instance, view_method, request, args, kwargs):
        return request.META


class QueryParamsKeyBit(KeyBitDictBase):
    """
    Return example:
        {'part': 'Londo', 'callback': 'jquery_callback'}

    """

    def get_source_dict(self, params, view_instance, view_method, request, args, kwargs):
        return request.GET


class PaginationKeyBit(QueryParamsKeyBit):
    """
    Return example:
        {'page_size': 100, 'page': '1'}

    """
    def get_data(self, **kwargs):
        kwargs['params'] = []
        if hasattr(kwargs['view_instance'], 'page_kwarg'):
            kwargs['params'].append(kwargs['view_instance'].page_kwarg)
        if hasattr(kwargs['view_instance'], 'paginate_by_param'):
            kwargs['params'].append(kwargs['view_instance'].paginate_by_param)
        return super(PaginationKeyBit, self).get_data(**kwargs)


class ListSqlQueryKeyBit(KeyBitBase):
    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        queryset = view_instance.filter_queryset(view_instance.get_queryset())
        if isinstance(queryset, EmptyQuerySet):
            return None
        else:
            return force_text(queryset.query.__str__())


class RetrieveSqlQueryKeyBit(KeyBitBase):
    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        lookup_value = view_instance.kwargs[view_instance.lookup_field]
        try:
            queryset = view_instance.filter_queryset(view_instance.get_queryset()).filter(
                **{view_instance.lookup_field: lookup_value}
            )
            if isinstance(queryset, EmptyQuerySet):
                return None
            else:
                return force_text(queryset.query.__str__())
        except ValueError:
            return None


class ArgsKeyBit(KeyBitBase):
    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        if self.params is not None:
            return [args[i] for i in self.params]
        return args


class KwargsKeyBit(KeyBitDictBase):
    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        # if no parameters specified, then get data for all kwargs
        return super(KwargsKeyBit, self).get_data(
            params=params or kwargs.keys(),
            view_instance=view_instance,
            view_method=view_method,
            request=request,
            args=args,
            kwargs=kwargs
        )

    def get_source_dict(self, params, view_instance, view_method, request, args, kwargs):
        return kwargs
