#ifndef DBIMPORTER_H
#define DBIMPORTER_H
#include <QObject>
#include <QSqlDatabase>
#include <QString>


class DbImporter:public QObject
{
    Q_OBJECT

public:
    explicit DbImporter(QObject *parent = nullptr);
    ~DbImporter();

    QString getDatabasePath() const;
    QString getExperimentName() const;

public slots:
    bool importDatabase();

signals:
    void importSucceeded(const QString &experimentName,const QStringList &videoList);
    void importFailed(const QString &errorMessage);

private:
    QString m_dbFilePath;
    QString m_experimentName;
    QSqlDatabase m_db;
    bool loadDataFromDatabase();
    QStringList videoList;

};

#endif // DBIMPORTER_H
