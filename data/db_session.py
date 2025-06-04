import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

# базовый класс для всех моделей ORM
SqlAlchemyBase = dec.declarative_base()

# для создания сессий базы данных
__factory = None

def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    # подключение к SQLite
    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'

    # создание движка базы данных
    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    # импорт всех моделей таблиц
    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)

def create_session() -> Session:
    global __factory
    return __factory()
