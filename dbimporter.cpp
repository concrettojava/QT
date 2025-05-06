#include "DbImporter.h"
#include <QFileDialog>
#include <QFileInfo>
#include <QSqlError>
#include <QDebug>
#include <QSqlQuery>

DbImporter::DbImporter(QObject *parent)
    :QObject(parent){}

DbImporter::~DbImporter()
{
    if (m_db.isOpen()){
            m_db.close();
        }
}

bool DbImporter::importDatabase()
{
    QString dbFilePath = QFileDialog::getOpenFileName(nullptr,"选择数据库文件",QDir::homePath(),"SQLite数据库(*.db *.sqlite);;所有文件(*.*)");

    if(dbFilePath.isEmpty()){
        return false;
    }
    m_dbFilePath = dbFilePath;

    //提取实验名称(使用文件名)
    QFileInfo fileInfo(dbFilePath);
    m_experimentName = fileInfo.baseName();

    //尝试打开数据库
    m_db = QSqlDatabase::addDatabase("QSQLITE");
    m_db.setDatabaseName(dbFilePath);

    if(!m_db.open()){
        emit importFailed(QString("无法打开数据库:%1").arg(m_db.lastError().text()));
        return false;
    }

    if (!loadDataFromDatabase()){
        emit importFailed(QString("加载数据失败"));
        return false;
    }

    emit importSucceeded(m_experimentName,videoList);
    return true;
}

bool DbImporter::loadDataFromDatabase(){
    if (!m_db.isOpen()){
        return false;
    }

    QStringList tabels = m_db.tables();
    qDebug() <<"数据库中的表："<<tabels;

    videoList.clear();
    if (tabels.contains("experiments")){
        QSqlQuery query("select file_path from video_data");
        while(query.next()){
            // 读取文件路径
            QString filePath = query.value("file_path").toString();
            //添加到字符串数组
            videoList.append(filePath);

            qDebug() <<"添加视频路径："<<filePath;
        }
         qDebug() << "共加载" << videoList.size() << "个视频文件路径";
    }
    else{
        qDebug() <<"数据库中没有找到video_data表!";
        return false;
    }

    return true;
}

QString DbImporter::getExperimentName() const{
    return m_experimentName;
}
