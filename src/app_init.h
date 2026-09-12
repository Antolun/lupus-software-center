#pragma once

#include <memory>
#include <QtGui/QGuiApplication>

std::unique_ptr<QGuiApplication> create_qapplication();
