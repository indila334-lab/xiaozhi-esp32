#ifndef REMOTE_EMOJI_LOADER_H
#define REMOTE_EMOJI_LOADER_H

#include "lvgl_image.h"

#include <memory>
#include <string>

class RemoteEmojiLoader {
public:
    static std::unique_ptr<LvglImage> Load(const std::string& url);
};

#endif
