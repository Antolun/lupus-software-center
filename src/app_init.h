#pragma once

#include <memory>
#include <cstring>
#include <cstdlib>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <QtGui/QGuiApplication>

// Creates and returns the QApplication instance.
std::unique_ptr<QGuiApplication> create_qapplication();

// Single-instance guard using a per-user Unix socket.
// If send_activate is true, sends "activate" to the running instance before returning false.
// Returns true  → first instance, proceed.
// Returns false → another instance was running; caller should exit.
extern "C" bool acquire_single_instance(bool send_activate);

// Updates application name, display name, and emits NewTitle on D-Bus for StatusNotifierItem (system tray)
extern "C" void set_application_title(const char* title);
