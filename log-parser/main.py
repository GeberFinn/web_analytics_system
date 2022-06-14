import os
import re

import pyspark
from pyspark.sql.functions import split
from pyspark.sql.types import *
from pprint import pprint
import pandas as pd

import numpy as np
# This is a sample Python script.
from pyspark.sql import Row
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

def file_preparing(path:str):
    cmd = f'tail -n +3 {path} > tmp.csv' # && mv tmp.csv books.csv
    #regex = r'''^(\d*-\d*-\d*\s\d*:\d*:\d*)\s-*(?:[\sINFO](INFO):\s*(\d*.\d*)\s*\|\s{1,5}(\s|[A-Z]*:)\s(.*)\s\bin\s(.*)\n|(?:[\sEMERGENCY](EMERGENCY):\s*(.*)|(?:[\sDEBUG](DEBUG):\s((#\d.*\n)*)|(?:[\sWARNING](WARNING):(.*):\s(.*)\s\bin\s)(.*))))'''
    regex = r'''^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})\s-*\s([A-Z]{3,}):\s((.*\n)*?(?=^([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})|$))'''
    info_regex = r'''(\d*.\d*)\s*\|\s{1,}(\s|[A-Z]*:)((.*(\n|\s))*)in (.*)'''
    emerg_regex = r'''(.*?):((.*(\n|\s))*)in (.*)'''
    warn_regex = r'''(.*?):((.*(\n|\s))*)in (.*)'''
    debug_regex = r'''((.*(\n|\s))*)in (.*)'''

    data_schema = [
        StructField('dtlogged',StringType(),False),
        StructField('vcstatus',StringType(),False),
        StructField('vcdesc',StringType(),False),
    ]

    struct = StructType(fields=data_schema)

    from clickhouse_driver import Client

    client = Client(host='localhost', port=9000,user='default', settings={'use_numpy': True})

    with open(path) as f:
        #print(f.seek(0, 2))
        #f.write("\n")
        list_b = []
        log_list = []
        parsed_log_list = []
        log_start_index = None


        for i,line in enumerate(f):
            #print(i,line)
            if re.match(r'^\d{4}', line):
                #if log_start_index:

                log_list.append(line)
                log_start_index = len(log_list)-1
                #print(log_list)
            elif log_start_index:
                #print(str(log_start_index) + ' X ' + line)
                log_list[log_start_index] = log_list[log_start_index] + line

            #else:
            #    pprint('ELSE '+line)

        log_list[-1]+="\n"

        log_df = pd.DataFrame(log_list,columns=['raw'])

        #df.memory_usage(deep=True)

        #list_df = np.array_split(df, n)

        #ddf = pd.DataFrame([],columns=['id','dtlogged','vcstatus', 'vcdesc'])
        #ddf.memory_usage(deep=True)
        #.memory_usage(deep=True) #df[['id','dtlogged','vcstatus', 'vcdesc']] = df['raw'].str.split(regex, expand=True).iloc[:, :4]  # ['0','1','2','3'])

        n = 200000
        list_df = [log_df[i:i + n] for i in range(0, log_df.shape[0], n)]

        ddf_list = []
        for df in list_df:
            ddf = df['raw'].str.split(regex, expand=True).iloc[:, :4]
            ddf.columns = ['id', 'dtlogged', 'vcstatus', 'vcdesc']
            status_df_list = []

            info_df = ddf.loc[ddf['vcstatus']=='INFO']
            if not info_df.empty:
                info_df = info_df.join(info_df['vcdesc'].str.split(info_regex,expand=True).iloc[:,[1,2,3,6]]) #[0, 1,2,3,6]
                info_df.drop('vcdesc',inplace=True, axis=1)
                info_df.columns = ['id', 'dtlogged', 'vcstatus','dduration', 'vctype', 'vcdesc', 'vcpath']
                info_df.loc[info_df['vctype']==' ','vctype'] = np.NaN
                status_df_list.append(info_df)

            emerg_df = ddf.loc[ddf['vcstatus'] == 'EMERGENCY']
            if not emerg_df.empty:
                emerg_df = emerg_df.join(emerg_df['vcdesc'].str.split(emerg_regex, expand=True).iloc[:, [1,2,5]])  # [0, 1,2,3,6]
                emerg_df.insert(3,"dduration",np.NaN)
                emerg_df.drop('vcdesc',inplace=True, axis=1)
                emerg_df.columns = ['id', 'dtlogged', 'vcstatus','dduration', 'vctype', 'vcdesc', 'vcpath']
                status_df_list.append(emerg_df)

            warn_df = ddf.loc[ddf['vcstatus'] == 'WARNING']
            if not warn_df.empty:
                warn_df = warn_df.join(warn_df['vcdesc'].str.split(warn_regex, expand=True).iloc[:, [1, 2, 5]])  # [0, 1,2,3,6]
                warn_df.insert(3, "dduration", np.NaN)
                warn_df.drop('vcdesc', inplace=True, axis=1)
                warn_df.columns = ['id', 'dtlogged', 'vcstatus', 'dduration', 'vctype', 'vcdesc', 'vcpath']
                status_df_list.append(warn_df)

            debug_df = ddf.loc[ddf['vcstatus'] == 'DEBUG']
            if not debug_df.empty:
                debug_df = debug_df.join(debug_df['vcdesc'].str.split(debug_regex, expand=True).iloc[:, [1,4]])  # [1, 2, 5] [0, 1,2,3,6]
                debug_df.insert(3, "dduration", np.NaN)
                debug_df.insert(4, "vctype", np.NaN)
                debug_df.drop('vcdesc', inplace=True, axis=1)
                debug_df.columns = ['id', 'dtlogged', 'vcstatus', 'dduration', 'vctype', 'vcdesc', 'vcpath']
                status_df_list.append(debug_df)


            result_chunk_df = pd.concat(status_df_list).sort_index()#.sort_values(by=['id'], ascending=False)

            #     info_df = info_df.astype(dtype= {"id":"int64",
        # "dtlogged":"datetime64", "vcstatus":"object", "dduration":"float64", "vctype":"object", "vcdesc":"object", "vcpath":"object"})

            #print(info_df)

            #print(result_chunk_df)



            ddf_list.append(result_chunk_df)




            #ddf = pd.concat([ddf,df['raw'].str.split(regex, expand=True).iloc[:, :4]])
            #pprint(df)

        res_df = pd.concat(ddf_list)
        pprint(res_df)

        print(log_df.shape[0])
        print(res_df.shape[0])

        client.insert_dataframe(f"INSERT INTO test_db.detailed_logs VALUES", res_df)

if __name__ == '__main__':
    from pyspark.sql import SparkSession

    # spark = SparkSession.builder \
    #     .master("local[*]") \
    #     .appName('LogParser') \
    #     .getOrCreate()

    log_file = './logs/05/01.php'
    file_preparing(log_file)


        #pprint(len(list_df))

        #df[['dtlogged','vcstatus', 'vcdesc']] = \
        #pprint(df['raw'].str.split(regex, expand=True).iloc[:,:4])#['0','1','2','3'])

        #pprint(df)

        #for log in log_list:
        #    for matchNum, match in enumerate(re.finditer(regex, log, re.MULTILINE),start=1):
        #        parsed_log_list.append([match[1],match[2],match[3]])

                # parsed_log_list.append([[match.group(1), match.group(2), match.group(3)] for matchNum, match in
                #                     enumerate(re.finditer(regex, log, re.MULTILINE),
                #                               start=1)])

        #print(parsed_log_list)
        #parsed_log_list = [x[0] for x in parsed_log_list[:]]

        # [[match.group(1), match.group(2), match.group(3)] for matchNum, match in
        #                      enumerate(re.finditer(regex, log, re.MULTILINE),
        #                                start=1)]

        #df = pd.DataFrame( [[match.group(1), match.group(2), match.group(3)] for matchNum, match in
        #                     enumerate(re.finditer(regex, log_list, re.MULTILINE),
        #                               start=1)],columns=['dtlogged','vcstatus', 'vcdesc']) #columns=['dtlogged', 'vcstatus', 'vcdesc'])

        #df['dtlogged'] = df['raw'].str.split(regex,
        #                          expand=True)

        #pprint(df)

        # matches = [[match.group(1), match.group(2), match.group(3)] for matchNum, match in
        #           enumerate(re.finditer(regex, line, re.MULTILINE),
        #                     start=1)]  # re.finditer(regex,content,re.MULTILINE)]

        #content = f.read()
        #result = re.split(regex, content,re.MULTILINE,re.IGNORECASE)

        #pattern = re.compile(regex,flags=re.MULTILINE)

        #matches = pattern.findall(content)

            #print(matches)

        #rdd = spark.sparkContext.emptyRDD()
        #spark.sparkContext.parallelize([Row(*matches)]).toDF().show()



#
            #df = pd.DataFrame(matches,columns=['dtlogged','vcstatus','vcdesc'])
            #client.insert_dataframe(f"INSERT INTO test_db.logs VALUES", df)

            #print(df)



        #df = spark.createDataFrame(matches,struct)
        #df.describe()

        #df2 = spark.createDataFrame([], schema)
        #df2.printSchema()

        #matches = re.finditer(regex, content, re.MULTILINE)

#        for matchNum, match in enumerate(matches, start=1):
#
#            #print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum, start=match.start(),
#            #                                                                    end=match.end(), match=match.group()))
#            log_dt = match.group(1)
#            log_status = match.group(2)
#            log_desc = match.group(3)
#
#
#
#            print(log_dt)
#            print(log_status)
#            print(log_desc)
#
#            #for groupNum in range(3): #0, len(match.groups())):
#            #    groupNum = groupNum + 1


                #print("Group {groupNum} found at {start}-{end}: {group}".format(groupNum=groupNum,
                #                                                                start=match.start(groupNum),
                #                                                                end=match.end(groupNum),
                #                                                                group=match.group(groupNum)))

        #print(result)


    #os.system(cmd)

    #adsample = spark.textFile("./1.csv")
    #splitted_sample = adsample.flatMap(lambda (x): ((v) for v in re.split('\s+(?=\w+=)', x)))

    #df = spark.read.csv(path,multiLine=True).show()

    #df = spark.createDataFrame([('oneAtwoBthreeC',)], ['s', ])
    #df.select(split(df.s, '[ABC]', 2).alias('s')).collect()

    #print(df)

# Press the green button in the gutter to run the script.


   # print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
