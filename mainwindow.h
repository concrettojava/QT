#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <dbimporter.h>
#include "videoplayer.h"

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:

    //导入成功处理
    void onImportSucceeded(const QString &experimentName,const QStringList &videoList);
    //导入失败处理
    void onImportFailed(const QString &errorMessage);
    //画面切换相应
    void btnSingleClicked();
    void btnMainClicked();
    void btnGlobalClicked();


private:
    Ui::MainWindow *ui;

    DbImporter *m_dbImporter;
    void updateUI();
    VideoPlayer *m_videoPlayer = nullptr;
    // VideoPlayer *m_videoPlayer;
};
#endif // MAINWINDOW_H
