import reprlib
from brine.exceptions import BrineError


class Schema(object):

    def __init__(self):
        self.columns = []

    def __repr__(self):
        return 'Schema(columns=%s)' % repr(self.columns)

    def add_column(self, name, column_type):
        self.append_column(Column(name, column_type))

    def append_column(self, column):
        column.set_index(len(self.columns))
        self.columns.append(column)

    def to_obj(self):
        return [column.to_obj() for column in self.columns]

    @classmethod
    def from_obj(cls, obj):
        schema = cls()
        for column_obj in obj:
            schema.append_column(Column.from_obj(column_obj))
        return schema


class Column(object):

    def __init__(self, name, column_type):
        self.name = name
        self.column_type = column_type
        self.index = None

    def __repr__(self):
        if self.categories:
            return 'Column(name=%s, type=%s, categories=%s)' % (
                self.name, reprlib.repr(self.column_type), reprlib.repr(self.categories))
        else:
            return 'Column(name=%s, type=%s)' % (self.name, repr(self.column_type))

    def isarray(self):
        return isinstance(self.column_type, (IntegerArray, FloatArray, CategoryArray))

    @property
    def categories(self):
        if not isinstance(self.column_type, (Category, CategoryArray)):
            return None
        return self.column_type.categories

    def isimage(self):
        return isinstance(self.column_type, Image)

    def set_index(self, index):
        self.index = index

    def to_obj(self):
        if isinstance(self.column_type, Integer):
            return {'name': self.name, 'type': 'integer'}
        elif isinstance(self.column_type, Float):
            return {'name': self.name, 'type': 'float'}
        elif isinstance(self.column_type, Category):
            return {'name': self.name, 'type': 'category', 'categories': self.column_type.categories}
        elif isinstance(self.column_type, String):
            return {'name': self.name, 'type': 'string'}
        elif isinstance(self.column_type, Image):
            return {'name': self.name, 'type': 'image'}
        elif isinstance(self.column_type, IntegerArray):
            return {'name': self.name, 'type': 'integer_array'}
        elif isinstance(self.column_type, FloatArray):
            return {'name': self.name, 'type': 'float_array'}
        elif isinstance(self.column_type, CategoryArray):
            return {'name': self.name, 'type': 'category_array', 'categories': self.column_type.categories}

    @classmethod
    def from_obj(cls, obj):
        name = obj.get('name')
        column_type = obj.get('type')
        if column_type == 'integer':
            return cls(name, Integer())
        elif column_type == 'float':
            return cls(name, Float())
        elif column_type == 'category':
            categories = obj.get('categories')
            return cls(name, Category(categories))
        elif column_type == 'string':
            return cls(name, String())
        elif column_type == 'image':
            return cls(name, Image())
        elif column_type == 'integer_array':
            return cls(name, IntegerArray())
        elif column_type == 'float_array':
            return cls(name, FloatArray())
        elif column_type == 'category_array':
            categories = obj.get('categories')
            return cls(name, CategoryArray(categories))


class ColumnType(object):
    pass


class Integer(ColumnType):

    def __repr__(self):
        return 'Integer'


class Float(ColumnType):

    def __repr__(self):
        return 'Float'


class Category(ColumnType):

    def __init__(self, categories):
        self.categories = categories

    def __repr__(self):
        return 'Category'


class String(ColumnType):

    def __repr__(self):
        return 'String'


class Image(ColumnType):

    def __repr__(self):
        return 'Image'


class IntegerArray(ColumnType):

    def __repr__(self):
        return 'IntegerArray'


class FloatArray(ColumnType):

    def __repr__(self):
        return 'FloatArray'


class CategoryArray(ColumnType):

    def __init__(self, categories):
        self.categories = categories

    def __repr__(self):
        return 'CategoryArray'


class SchemaError(BrineError):
    pass
