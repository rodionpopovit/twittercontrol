import psycopg2

from .configuration import ConfigurationException

DB_CONNECT_STRING = "host='{host}' dbname='{dbname}' user='{user}' password='{passwd}'"

class DBItemCompany:
    def __init__(self, _id, tweeter, category, categoryUrl, provenScore, ranking, location, url, categoryId):
        self.id = _id
        self.twitterAccount = tweeter
        self.category = category
        self.categoryUrl = categoryUrl
        self.provenScore = provenScore
        self.ranking = ranking
        self.location = location
        self.url = url
        self.categoryId = categoryId

    @property
    def invalidScore(self):
        return self.provenScore is None or self.provenScore < 1

    @property
    def twitter(self):
        return '@' + self.twitterAccount

class DBException(Exception):
    """
    Represents a generic exception thrown by the Database Manager
    """
    pass

class DBManager:
    def __init__(self, cfg):
        self.cfg = cfg

        self.__companies = {}
        self.__loggedIn = False
        self.connection = None
        self.cursor = None

    def __del__(self):
        try:
            self.connection.close()
        except psycopg2.Error:
            pass

    def __logInDb(self):
        try:
            dbSettings = self.cfg.databaseSettings

            self.connection = psycopg2.connect(DB_CONNECT_STRING.format(
                host=dbSettings[0], dbname=dbSettings[1],
                user=dbSettings[2], passwd=dbSettings[3]
            ))
            self.cursor = self.connection.cursor()

            self.__loggedIn = True

            return True
        except (psycopg2.OperationalError, ConfigurationException):
            return False

    def __getDomainName(self, schema):
        try:
            self.cursor.execute("SELECT domain_url FROM customers_customer WHERE schema_name='{schemaname}'".format(schemaname=schema))
            return 'http://' + self.cursor.fetchone()[0]
        except psycopg2.DatabaseError:
            raise DBException('Failed to extract domain name from database')

    def __buildCategoryUrl(self, catId, schemaName):
        return '{domain}/vendors/?find=category-{categoryId}'.format(domain=self.__getDomainName(schemaName), categoryId=catId)

    def __buildProfileUrl(self, catSlug, profSlug, schemaName):
        return '{domain}/vendors/{categorySlug}/{profileSlug}'.format(domain=self.__getDomainName(schemaName),
                                                                        categorySlug=catSlug,
                                                                        profileSlug=profSlug)

    def __buildProfileUrlWOCategory(self, profSlug, schemaName):
        return '{domain}/vendors/{profileSlug}'.format(domain=self.__getDomainName(schemaName), profileSlug=profSlug)

    def __getCompaniesData(self, schema):
        """
        Load Companies list from database
        """
        try:
            self.cursor.execute("""SELECT id, twitter, proven_score, slug FROM {schema}.vendors_vendor WHERE
                                twitter <> ''""".format(schema=schema))
            data = self.cursor.fetchall()

            companies = []
            for entry in data:
                self.cursor.execute('SELECT location_id FROM {schema}.vendors_vendorlocation WHERE vendor_id = {vendor}'.format(schema=schema, vendor=entry[0]))
                cities = self.cursor.fetchall()

                if cities is None:
                    continue

                city = ''

                for cityId in cities:
                    self.cursor.execute('SELECT city FROM {schema}.locations_location WHERE id = {city}'.format(schema=schema, city=cityId[0]))
                    cityName = self.cursor.fetchone()

                    if cityName is not None:
                        city += cityName[0]

                self.cursor.execute('SELECT category_id, rank FROM {schema}.vendors_vendorcustomkind WHERE vendor_id = {vendor} AND "primary" is true'.format(schema=schema, vendor=entry[0]))
                customKind = self.cursor.fetchone()

                if customKind is None:
                    catId = rank = None
                else:
                    catId, rank = customKind

                if catId is not None:
                    self.cursor.execute('SELECT name, slug FROM {schema}.categories_category WHERE id = {cat}'.format(schema=schema, cat=catId))
                    catData = self.cursor.fetchone()
                else:
                    catData = None

                companies.append(DBItemCompany(
                    _id         = entry[0],
                    tweeter     = entry[1],
                    category    = catData[0] if catData is not None else None,
                    categoryUrl = self.__buildCategoryUrl(catId, schema) if catId is not None else None,
                    provenScore = entry[2],
                    ranking     = rank,
                    location    = city,
                    url         = self.__buildProfileUrl(catData[1], entry[3], schema) if catData is not None else self.__buildProfileUrlWOCategory(entry[3], schema),
                    categoryId  = catId
                ))

            self.__companies[schema] = companies

        except psycopg2.DatabaseError as err:
            raise DBException(err.args[0])

    def domainUrl(self, schema):
        return self.__getDomainName(schema)

    def refreshData(self, schemas):
        if not self.__loggedIn:
            if not self.__logInDb():
                return False

        for schema in schemas:
            self.__getCompaniesData(schema)

        return True

    @property
    def companies(self):
        return self.__companies

    @property
    def isConnected(self):
        return self.__loggedIn
