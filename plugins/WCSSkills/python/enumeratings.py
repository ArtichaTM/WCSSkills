from enum import EnumMeta
class Tuple_Enum_Meta(EnumMeta):
    def __call__(cls, value, *args, **kwargs):
        for enum_variable in iter(cls):
            if enum_variable.value[0] == value:
                return enum_variable