
from clickhouse_driver import Client




import sys
import psycopg2
from config import load_config
from contextlib import closing
from psycopg2.extras import DictCursor


config = load_config()
db = config.db
host = config.host
user = config.user
password = config.password
port = config.port

def insert_answer(ichatid, iquestionid, ianswerid, vcanswer):
    try:
        # connection = psycopg2.connect(dbname = db,user = user,password = password,host = host)
        with closing(psycopg2.connect(dbname=db, user=user, password=password, host=host)) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = f'''INSERT INTO rtb.account_chat_answer
    	        (ichatid, iquestionid, ianswerid, vcanswer)
    	            VALUES (%s, %s, %s, %s);
                                '''
                cursor.execute(query, (ichatid, iquestionid, ianswerid, vcanswer))

                conn.commit()

    except:
        e = sys.exc_info()
        print(e)
        print(f"Ploblems with connection to:\n* {str(host)}\n* {str(db)}\n* {query}")
        conn.rollback()



def insert_account_chat(iaccountid,dtstart,istateid):
    try:
        # connection = psycopg2.connect(dbname = db,user = user,password = password,host = host)
        with closing(psycopg2.connect(dbname=db, user=user, password=password, host=host)) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = f'''INSERT INTO rtb.account_chat
	        (iaccountid, dtstart, istateid)
	            SELECT iaccountid,%s,%s 
	                FROM rtb.account WHERE itgid = %s
                    RETURNING ichatid
                            '''
                cursor.execute(query, (dtstart, istateid, iaccountid,))
                records = cursor.fetchall()
                conn.commit()
                return records[0][0]


    except:
        e = sys.exc_info()
        print(e)
        print(f"Ploblems with connection to:\n* {str(host)}\n* {str(db)}\n* {query}")
        conn.rollback()



def get_question_info(cq):
    try:
        # connection = psycopg2.connect(dbname = db,user = user,password = password,host = host)
        with closing(psycopg2.connect(dbname=db, user=user, password=password, host=host)) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:

                query = '''SELECT * FROM rtb.question 
                                    WHERE iquestionid = %s
                        '''

                cursor.execute(query, (cq,))
                records = cursor.fetchall()
                return records

    except:
        e = sys.exc_info()
        print(e)
        print("Ploblems with connection to:\n " + str(host) + "\n" + str(db))



def check_user_id(id):


        #print(db,user,host)
        #connection = psycopg2.connect(dbname = db,user = user,password = password,host = host)
        #print(connection)
    with closing(psycopg2.connect(dbname=db, user=user, password=password, host=host,port=port)) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:

            query = '''SELECT * FROM rtb.account 
                                    WHERE itgid = %s
                        '''

            cursor.execute(query, (id,))

            records = cursor.fetchall()

            if not records:
                return 0
            else:
                return records
    #except Exception as e:
    #    print(f"Ploblems with connection to:\n* {str(host)}\n* {str(db)}\n* {e.args}") #{query}")



def check_user_phone(phone):
    try:
        # connection = psycopg2.connect(dbname = db,user = user,password = password,host = host)
        with closing(psycopg2.connect(dbname=db, user=user, password=password, host=host)) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:

                query = '''SELECT * FROM rtb.account 
                                    WHERE vcphone = %s
                        '''
                cursor.execute(query, (phone,))

                records = cursor.fetchall()

                if not records:
                    return 0
                else:
                    return records

                # records = 'Не найдено'


    except:
        print("Ploblems with connection to:\n " + str(host) + "\n" + str(db))


def update_account_id(id, ac_id):
    try:
        # connection = psycopg2.connect(dbname = db,user = user,password = password,host = host)
        with closing(psycopg2.connect(dbname=db, user=user, password=password, host=host)) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = '''UPDATE rtb.account
                    SET  itgid=%s WHERE iaccountid=%s'''

                cursor.execute(query, (id, ac_id,))
                print(query)
                conn.commit()

    except:

        print(f"Ploblems with connection to:\n* {str(host)}\n* {str(db)}\n* {query}")
        conn.rollback()


def get_next_question(cq, ca):
    try:
        with closing(psycopg2.connect(dbname=db, user=user, password=password, host=host)) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:

                query = '''SELECT * FROM rtb.question_map
                                    WHERE iprev_questionid = %s AND (ianswerid IS NULL or ianswerid = %s)
                        '''
                cursor.execute(query, (cq, ca, ))
                records = cursor.fetchall()
                if not records:
                    return 0
                else:
                    return records
    except:
        print("Ploblems with connection to:\n " + str(host) + "\n" + str(db))


def get_buttons(question_id):
    try:
        # connection = psycopg2.connect(dbname = db,user = user,password = password,host = host)
        with closing(psycopg2.connect(dbname=db, user=user, password=password, host=host)) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:

                query = '''SELECT * FROM rtb.answer 
	                            WHERE iquestionid = %s ;
                        '''
                cursor.execute(query, (question_id, ))

                records = cursor.fetchall()

                if not records:
                    return 0
                else:
                    return records

                # records = 'Не найдено'

    except:
        print("Ploblems with connection to:\n " + str(host) + "\n" + str(db))


def get_answer_info(answer_id):
    try:
        # connection = psycopg2.connect(dbname = db,user = user,password = password,host = host)
        with closing(psycopg2.connect(dbname=db, user=user, password=password, host=host)) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:

                query = '''SELECT * FROM rtb.answer
                                    WHERE ianswerid = %s ;
                        '''
                cursor.execute(query, (answer_id, ))

                records = cursor.fetchall()

                if not records:
                    return 0
                else:
                    return records

    except:
        print("Ploblems with connection to:\n " + str(host) + "\n" + str(db))



# client = Client(host='localhost', port=9000,user='default', settings={'use_numpy': True})
#
# def get_column_name(db,table):
#     query = f'''select name from `system`.columns
#                 where 1=1
#                 and database='{db}'
#                 and table='{table}' '''
#
#     list = client.execute(query)
#
#     print(list)
#
# get_column_name(db='test_db',table='detailed_logs')