#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QMessageBox>
#include <QDebug>


MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
    ,m_dbImporter(new DbImporter)
{
    ui->setupUi(this);

    //链接导入按钮与dbImporter
    connect(ui->importButton,&QPushButton::clicked,m_dbImporter,&DbImporter::importDatabase);

    //处理DbImporter发送的数据导入成功或失败的信号
    connect(m_dbImporter,&DbImporter::importSucceeded,this,&MainWindow::onImportSucceeded);
    connect(m_dbImporter,&DbImporter::importFailed,this,&MainWindow::onImportFailed);

    // 初始化UI
    updateUI();
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::onImportSucceeded(const QString &experimentName,const QStringList &videoList)
{
    // 导入成功后的处理
    // QMessageBox::information(this, "导入成功", QString("实验名: %1").arg(experimentName));
    // 创建消息内容，包含实验名和视频列表
    QString message = QString("实验名: %1\n\n导入的视频:\n").arg(experimentName);

    // 添加视频列表到消息
    for (int i = 0; i < videoList.size(); i++) {
        message += QString("- %1\n").arg(videoList.at(i));
    }

    // 显示消息框
    QMessageBox::information(this, "导入成功", message);

    // 一步完成所有初始化
    m_videoPlayer = new VideoPlayer(this,&videoList);

    // 连接按钮
    connect(ui->singelViewButton, &QPushButton::clicked, m_videoPlayer, &VideoPlayer::playSingle);
    connect(ui->mainViewButton, &QPushButton::clicked, m_videoPlayer, &VideoPlayer::playMain);
    connect(ui->globalViewButton, &QPushButton::clicked, m_videoPlayer, &VideoPlayer::playGlobal);

    // 更新UI以反映新的数据
    updateUI();


}

void MainWindow::onImportFailed(const QString &errorMessage)
{
    // 导入失败后的处理
    QMessageBox::critical(this, "导入失败", errorMessage);
}

void MainWindow::updateUI(){
    ui->expNameLabel->setText(m_dbImporter->getExperimentName());
}

void MainWindow::btnSingleClicked(){
    qDebug() << "切换到单视角";
    m_videoPlayer->playSingle();
    ui->statusbar->showMessage("单视角回放");
}

void MainWindow::btnMainClicked(){
    qDebug() << "切换到高速摄像机视角";
    m_videoPlayer->playMain();
    ui->statusbar->showMessage("高速摄像机回放")
}

void MainWindow::btnGlobalClicked(){
    qDebug() << "切换到全部影像视角";
    m_videoPlayer->playGlobal();
    ui->statusbar->showMessage("全局视角");
}






