from googleapiclient.discovery import build
from pprint import pprint
import pymongo
import psycopg2
import pandas as pd
import streamlit as st 

api_key='AIzaSyDCdzYN3N-BrWiW4ZFr0rPyeuHndqWWi5c'
api_service_name="youtube"
api_version="v3"

youtube=build(api_service_name,api_version,developerKey=api_key)
request=youtube.channels().list(
    part="snippet,contentDetails,statistics",
    id="UCtVDQNGBmS8DTP5fPzM_GmQ"
)
response=request.execute()

#to get channel channel informations
def fetch_channel_info(channel_id):
    youtube=build(api_service_name,api_version,developerKey=api_key)
    request=youtube.channels().list(
    part="snippet,contentDetails,statistics",
    id=channel_id
    )
    response=request.execute()
    for i in response['items']:
        channel_data=dict(channel_name=i['snippet']['title'],
                        channel_id=i['id'],
                        s_count=i['statistics']['subscriberCount'],
                        channel_views=i['statistics']['viewCount'],
                        total_videos=i['statistics']['videoCount'],
                        channel_description=i['snippet']['description'],
                        playlist_id=i['contentDetails']['relatedPlaylists']['uploads'])
    return channel_data

#To get video id
def to_get_video_id(channel_id):
    list=[]
    youtube=build(api_service_name,api_version,developerKey=api_key)
    request=youtube.channels().list(part='contentDetails',id=channel_id)
    response=request.execute()
    playlist_id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    remaining_video_id=None

    while True:
        request1 = youtube.playlistItems().list(part='snippet', playlistId=playlist_id,maxResults=50,pageToken=remaining_video_id)
        response1=request1.execute()
        response1['items'][0]['snippet']['resourceId']['videoId']


        for i in range(len(response1['items'])):
            list.append(response1['items'][i]['snippet']['resourceId']['videoId'])

        remaining_video_id= response1.get('nextPageToken')
        if remaining_video_id is None:
          break
    return list

#to get video informations
def video_infromation(video_ids):
    list_video=[]
    for video_info in video_ids:
            request = youtube.videos().list(
            part="snippet,contentDetails,statistics",id=video_info
            )
            response= request.execute()
        
            for item in response['items']:
                video_data=dict(channel_name=item['snippet']['channelTitle'],
                                channel_Id=item['snippet']['channelId'],
                                video_id=item['id'],
                                video_Name=item['snippet']['title'],
                                tags=item['snippet'].get('tags'),
                                video_Description=item['snippet']['description'],
                                published_at=item['snippet']['publishedAt'],
                                view_count=item['statistics']['viewCount'],
                                like_count=item['statistics'].get('likeCount'),
                                dislike_count=item.get('dislike_count'),
                                favorite_count=item['statistics']['favoriteCount'],
                                comment_count=item.get('commentCount'),
                                duration=item['contentDetails']['duration'],
                                thumbnail=item['snippet']['thumbnails']['default']['url'])
            list_video.append(video_data)
    return list_video        


#TO GET COMMEND DETAILS
def comment_details(video_information):
    comment_list=[]
    try:
        for video_info in video_information:
            request = youtube.commentThreads().list(
                                            part="snippet,replies",
                                            videoId=video_info, 
                                            maxResults=50)
            response = request.execute()
                
            for value in response['items']:
                comment_data=dict(comment_id=value['snippet']['topLevelComment']['id'],
                                video_id=value['snippet']['videoId'],
                                comment_text=value['snippet']['topLevelComment']['snippet']['textDisplay'],
                                comment_author=value['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                                comment_publishedAt=value['snippet']['topLevelComment']['snippet']['publishedAt'])  
                
                comment_list.append(comment_data)
    except:
        pass    
    return comment_list     

client=pymongo.MongoClient("mongodb://localhost:27017")
db=client["youtube"]


#UPLOADING EVERYTHING TO MONGO_DB
def channel_info(channel_id):
    channel_details=fetch_channel_info(channel_id)
    video_id=to_get_video_id(channel_id)
    video_details=video_infromation(video_id)
    comment_detail=comment_details(video_id)
    
    collection1=db["channel_details"]
   
    collection1.insert_one({"channel_information":channel_details,
                            "video_information":video_details,
                            "comment_information":comment_detail})
    
    return"upload completed successfully "


#creating channel table to my sql 
def channels_table():
    mydb = psycopg2.connect(host="localhost",
            user="postgres",
            password="12345",
            database= "youtube_data",
            port = "5432"
            )
    cursor = mydb.cursor()


    drop_query='''drop table if exists channels'''
    cursor.execute(drop_query)
    mydb.commit()


    try:
        create_query = '''create table if not exists channels(Channel_Name varchar(100),
                        Channel_Id varchar(80) primary key, 
                        Subscription_Count bigint, 
                        Views bigint,
                        Total_Videos int,
                        Channel_Description text,
                        Playlist_Id varchar(50))'''
        cursor.execute(create_query)
        mydb.commit()
    except:
        print("Channels Table alredy created") 


    ch_list=[]
    db = client["youtube"]
    coll1 = db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data['channel_information'])
    df=pd.DataFrame(ch_list)

    for index,row in df.iterrows():
        insert_query = '''insert into channels(Channel_Name,
                                                Channel_Id,
                                                Subscription_Count,
                                                Views,
                                                Total_Videos,
                                                Channel_Description,
                                                Playlist_Id)
                                    
                                                values(%s,%s,%s,%s,%s,%s,%s)'''
        
        values =(
            row['channel_name'],
            row['channel_id'],
            row['s_count'],
            row['channel_views'],
            row['total_videos'],
            row['channel_description'],
            row['playlist_id'])

        try:                     
                cursor.execute(insert_query,values)
                mydb.commit() 

        except:
            print("channel values are already inserted")   


#creating video table to sql 
def videos_table():
        mydb = psycopg2.connect(host="localhost",
                user="postgres",
                password="12345",
                database= "youtube_data",
                port = "5432"
                )
        cursor = mydb.cursor()


        drop_query='''drop table if exists videos'''
        cursor.execute(drop_query)
        mydb.commit()


        create_query = '''create table if not exists videos(channel_name varchar(100),
                                                        channel_Id varchar(100),
                                                        video_id varchar(30) primary key,
                                                        video_Name varchar(150),
                                                        tags text,
                                                        video_Description text,
                                                        published_at timestamp,
                                                        view_count bigint,
                                                        like_count bigint,
                                                        dislike_count bigint,
                                                        favorite_count int,
                                                        comment_count int,
                                                        duration interval,
                                                        thumbnail varchar(200)
                                                        )'''
        cursor.execute(create_query)
        mydb.commit()
        
        vi_list=[]
        db = client["youtube"]
        coll1 = db["channel_details"]
        for vi_data in coll1.find({},{"_id":0,"video_information":1}):
            for i in range(len(vi_data["video_information"])):
                vi_list.append(vi_data["video_information"][i])
        df1=pd.DataFrame(vi_list)   


        for index,row in df1.iterrows():
                insert_query = '''insert into videos(channel_name ,
                                                        channel_Id,
                                                        video_id ,
                                                        video_Name ,
                                                        tags ,
                                                        video_Description ,
                                                        published_at ,
                                                        view_count ,
                                                        like_count ,
                                                        dislike_count ,
                                                        favorite_count ,
                                                        comment_count ,
                                                        duration ,
                                                        thumbnail 
                                                )
                                        
                                                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                
        
                values =(
                        row['channel_name'],
                        row['channel_Id'],
                        row['video_id'],
                        row['video_Name'], 
                        row['tags']  ,     
                        row['video_Description'],
                        row['published_at'],
                        row['view_count'],
                        row['like_count'],
                        row['dislike_count'],
                        row['favorite_count'],
                        row['comment_count'],
                        row['duration'],
                        row['thumbnail']
                        
                        )

                cursor.execute(insert_query,values)
                mydb.commit()
                
                
                
# inserting comment table to sql 
def comments_table():
    mydb = psycopg2.connect(host="localhost",
        user="postgres",
        password="12345",
        database= "youtube_data",
        port = "5432"
        )
    cursor = mydb.cursor()


    drop_query='''drop table if exists comments'''
    cursor.execute(drop_query)
    mydb.commit()


    create_query = '''create table if not exists comments(comment_id varchar(100) primary key,
                                    video_id varchar(50),
                                    comment_text text,
                                    comment_author varchar(150),
                                    comment_publishedAt timestamp
                                                )'''
    cursor.execute(create_query)
    mydb.commit()


    com_list=[]
    db = client["youtube"]
    coll1 = db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df2=pd.DataFrame(com_list)  


    for index,row in df2.iterrows():
            insert_query = '''insert into comments(comment_id  ,
                                    video_id ,
                                    comment_text ,
                                    comment_author ,
                                    comment_publishedAt)
                                        
                                    values(%s,%s,%s,%s,%s)'''
        
            values =(
                row['comment_id'],
                row['video_id'],
                row['comment_text'],
                row['comment_author'],
                row['comment_publishedAt'],
                    )

                            
            cursor.execute(insert_query,values)
            mydb.commit() 
    

def tables():
    channels_table()
    videos_table()
    comments_table()

    return "Tables Created Successfully "    

def show_channels_table():
    ch_list=[]
    db = client["youtube"]
    coll1 = db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data['channel_information'])
    df=st.dataframe(ch_list)

    return df

def show_videos_table():
  vi_list=[]
  db = client["youtube"]
  coll1 = db["channel_details"]
  for vi_data in coll1.find({},{"_id":0,"video_information":1}):
      for i in range(len(vi_data["video_information"])):
        vi_list.append(vi_data["video_information"][i])
  df1=st.dataframe(vi_list)  

  return df1 

    
def show_comments_table():
    com_list=[]
    db = client["youtube"]
    coll1 = db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df2=st.dataframe(com_list) 

    return df2


#streamlit part

with st.sidebar:
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header("Skill Take Away")
    st.caption("python scripting")
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption("Data management using MongoDB and SQL")

channel_id=st.text_input("Enter the channel ID")   

if st.button("collect and store data"):
    ch_ids=[]
    db=client["youtube"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_ids.append(ch_data["channel_information"]["channel_id"])
        
    if channel_id in ch_ids:
        st.success("channel Deatails of the given channel id already exists")

    else:
        insert=channel_info(channel_id)    
        st.success(insert)

if st.button("Migrate to sql"):
   Table=tables()
   st.success(Table)


show_table=st.radio("SELECT THE TABLE FOR VIEW",("CHANNELS","VIDEOS","COMMENTS"))


if show_table=="CHANNELS":
   show_channels_table()

elif show_table=="VIDEOS":
   show_videos_table()

elif show_table=="COMMENTS":
   show_comments_table()


#SQL CONNECTION

mydb = psycopg2.connect(host="localhost",
        user="postgres",
        password="12345",
        database= "youtube_data",
        port = "5432"
        )
cursor = mydb.cursor()

question=st.selectbox("Select your question",("1.All the videos and channel name ",
                                               "2.channel with most number of videos",
                                               "3.10 most viewed videos",
                                               "4.comments in each videos",
                                               "5.videos with highest likes",
                                               "6.likes of all videos",
                                               "7.views of each channel",
                                               "8.videos published in the year of 2022",
                                               "9.average duration of all videos in each channel",
                                               "10.videos with highest number of comments"
                                        ))

if question=="1.All the videos and channel name ":
        query1='''select video_name as videos,channel_name as channelname from videos'''
        cursor.execute(query1)
        mydb.commit()
        t1=cursor.fetchall()
        df=pd.DataFrame(t1,columns=["video title","channel name"])
        st.write(df)


elif question=="2.channel with most number of videos":
        query2='''select channel_name as channelname,total_videos as no_videos from channels
                order by total_videos desc'''
        cursor.execute(query2)
        mydb.commit()
        t2=cursor.fetchall()
        df1=pd.DataFrame(t2,columns=["channel name","No of videos"])
        st.write(df1)  


elif question=="3.10 most viewed videos":
        query3='''select view_count as views ,channel_name as channelname,video_name as videotitle from videos
                where view_count is not null order by views desc limit 10'''
        cursor.execute(query3)
        mydb.commit()
        t3=cursor.fetchall()
        df2=pd.DataFrame(t3,columns=["views","channel name","videotitle"])      
        st.write(df2)
elif question=="4.comments in each videos":
        query4='''select comment_count as no_comments,video_name  as videotitle from videos where comment_count is not null '''
        cursor.execute(query4)
        mydb.commit()
        t4=cursor.fetchall()
        df3=pd.DataFrame(t4,columns=["no of comments","videotitle"])
        st.write(df3)

elif question=="5.videos with highest likes":
        query5='''select video_name as videotitle ,channel_name as channelname,like_count as likecount
                from videos where like_count is not null order by like_count desc '''
        cursor.execute(query5)
        mydb.commit()
        t5=cursor.fetchall()
        df4=pd.DataFrame(t5,columns=["videotitle","channelname","likecount"])    
        st.write(df4)  

elif question=="6.likes of all videos":
        query6='''select like_count as likecounts ,video_name as videotitle from videos '''
        cursor.execute(query6)
        mydb.commit()
        t6=cursor.fetchall()
        df5=pd.DataFrame(t6,columns=["likecounts","videotitle"])  
        st.write(df5)

elif question=="7.views of each channel":
        query7='''select channel_name as channelname,views as totalviews from channels  '''
        cursor.execute(query7)
        mydb.commit()
        t7=cursor.fetchall()
        df6=pd.DataFrame(t7,columns=["channel name ","totalviews"])
        st.write(df6)    

elif question=="8.videos published in the year of 2022":
        query8='''select video_name as video_title,published_at as videorelease,channel_name as channelname from videos
                where extract (year from published_at)=2022 '''
        cursor.execute(query8)
        mydb.commit()
        t8=cursor.fetchall()
        df7=pd.DataFrame(t8,columns=["videotitle","published_at","channelname"])
        st.write(df7)   


elif question=="9.average duration of all videos in each channel":
        query9='''select channel_name as channelname,AVG(duration ) as averageduration from videos group by channel_name'''
        cursor.execute(query9)
        mydb.commit()
        t9=cursor.fetchall()
        df8=pd.DataFrame(t9,columns=["channelname ","averageduration"])
        df8



        T9 = []
        for index, row in df8.iterrows():
                channel_title = row["channelname "].strip()  # Strip leading/trailing whitespace
                average_duration = row["averageduration"]
                average_duration_str = str(average_duration)
                T9.append({"channelname": channel_title, "averageduration": average_duration_str})
                df8=pd.DataFrame(T9)
                st.write(df8)



elif question=="10.videos with highest number of comments":
        query10='''select video_name as videotitle ,channel_name as channelname ,comment_count as comments from videos where comment_count is 
                not null order by comments desc '''
        cursor.execute(query10)
        mydb.commit()
        t10=cursor.fetchall()
        df9=pd.DataFrame(t10,columns=["videotitle ","channelname","comments"])
        st.write(df9)








    


