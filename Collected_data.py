import pandas as pd
from sqlalchemy import create_engine
import json
from sqlalchemy import text


class Database:

    def __init__(self):
        with open(r'D:\HULK\builds\Reports\config.json') as config_file:
            config = json.load(config_file)
        db_config = config['db']
        self.connection_string = f'mssql+pymssql://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}/{db_config["database"]}'
        self.engine = create_engine(self.connection_string)
        self.conn = self.engine.connect()

    def close_connection(self):
        self.conn.close()

# get testers name and type
    def get_collected_data_rows(self, serial):
        """
        :param serial:
        :return: list of dictionaries that every dict is a table.
        the key "ID" at every dict is need to be sending to the next function to get his data
        """
        query = text(f"""SELECT Collected_Data.ID, Start_Time, Testers.Name AS Tester_Name, Stations.Name, Serial_No, Result_Text, Work_Order, ISNULL(Cat_No.Cat_No+' '+Cat_No.Name,Collected_Data.Cat_No) AS Cat, Revision, round(Collected_Data.Test_Time,2) AS Test_Time,Failed_Step, Failed_SSID, Tester_SW_Version, Type
                    FROM Collected_Data 
                    JOIN Testers ON Collected_Data.Tester_ID=Testers.ID
                    JOIN Testers_Types ON Testers.Type_ID=Testers_Types.ID
                    LEFT JOIN Stations ON Collected_Data.Station_ID=Stations.ID
                    LEFT JOIN Cat_No ON Collected_Data.Cat_No = Cat_No.Cat_No
                    WHERE 
                    Serial_No LIKE '{serial}%'
                    ORDER BY Collected_Data.ID
                    """)
        print()
        df = pd.read_sql_query(query, self.conn)
        headers = list(df.columns)
        return df, headers

    def get_data_per_row(self, row):
        query = text(f"""SELECT Test_Name, '', Result, Results_Data.Low_Limit, Results_Data.High_Limit, Step_Parameter, Step_Info, Step_Start_Time, Step_Time, Result_Step_ID_Name, Test_ID
                    FROM Results_Data
                    WHERE 
                    Collected_Data_ID={row}
                    ORDER BY Results_Data.ID""")
        print(query)
        df = pd.read_sql_query(query, self.conn)
        headers = list(df.columns)
        return df, headers

