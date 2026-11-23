
from services.db import Db
from abc import ABCMeta, abstractmethod


class ActiveRecordEntity(metaclass=ABCMeta):
    _id = None

    def get_id(self):
        return self._id

    def save(self):
        mapped_properties = self.map_properties_to_db_format()

        if self._id is not None:
            self.update(mapped_properties)
        else:
            self.insert(mapped_properties)

    def delete(self):
        db = Db()
        table = self.__class__.get_table_name()

        db.query(
            f'DELETE FROM `{table}` WHERE id = :id',
            {'id': self._id}
        )

        self._id = None
        db.connection.commit()
        db.connection.close()

    @classmethod
    def find_all(cls):
        db = Db()
        table_name = cls.get_table_name()

        return db.query(
            f"SELECT * FROM `{table_name}`",
            {},
            cls
        )

    @classmethod
    def get_by_id(cls, id):
        db = Db()
        table_name = cls.get_table_name()

        result = db.query(
            f"SELECT * FROM `{table_name}` WHERE id = :id",
            {'id': id},
            cls
        )

        if result:
            return result[0]

        return None

    @classmethod
    def find_one_by_column(cls, column_name, value):
        db = Db()
        table_name = cls.get_table_name()

        # Название столбца должно быть доверенным,
        # значение передаётся через SQL-параметр.
        result = db.query(
            f"SELECT * FROM `{table_name}` "
            f"WHERE `{column_name}` = :value LIMIT 1",
            {'value': value},
            cls
        )

        if result:
            return result[0]

        return None

    @classmethod
    @abstractmethod
    def get_table_name(cls):
        pass

    def map_properties_to_db_format(self):
        properties = self.__dict__
        mapped_properties = {}

        for property_name, value in properties.items():
            property_name = property_name[1:]
            mapped_properties[property_name] = value

        return mapped_properties

    def to_dict(self):
        return self.map_properties_to_db_format()

    def update(self, mappedProperties):
        columns2params = []
        columns2values = {}
        index = 1

        for column, value in mappedProperties.items():
            param = f"param{index}"
            param_ext = ':' + param

            columns2params.append(f"`{column}` = {param_ext}")
            columns2values[param] = value
            index += 1

        sql = (
            f"UPDATE `{self.__class__.get_table_name()}` "
            f"SET {', '.join(columns2params)} "
            f"WHERE id = :id"
        )
        columns2values['id'] = self._id

        db = Db()
        db.query(sql, columns2values)
        db.connection.commit()
        db.connection.close()

    def insert(self, mappedProperties):
        filteredProperties = dict(
            filter(
                lambda item: item[1] is not None and item[1] != '',
                mappedProperties.items()
            )
        )

        columns = []
        paramsNames = []
        params2values = {}


        for columnName, value in filteredProperties.items():
            columns.append('`' + columnName + '`')
            paramsName = ':' + columnName
            paramsNames.append(paramsName)
            params2values[columnName] = value

        columnsViaSemicolon = ', '.join(columns)
        paramsNamesViaSemicolon = ', '.join(paramsNames)


        sql = (
            'INSERT INTO `' + self.__class__.get_table_name() + '` '
            '(' + columnsViaSemicolon + ') '
            'VALUES (' + paramsNamesViaSemicolon + ');'
        )


        db = Db()
        cursor = db.connection.cursor()
        cursor.execute(sql, params2values)

        self._id = cursor.lastrowid

        db.connection.commit()
        db.connection.close()

    @classmethod
    def search(cls, column, search_string):
        db = Db()
        table = cls.get_table_name()

        # Значения поиска передаются параметром.
        return db.query(
            f"SELECT * FROM `{table}` "
            f"WHERE `{column}` LIKE :search_string",
            {'search_string': f'%{search_string}%'},
            cls
        )
