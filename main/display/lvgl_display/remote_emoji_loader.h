#ifndef REMOTE_EMOJI_LOADER_H
#define REMOTE_EMOJI_LOADER_H

#include "lvgl_image.h"
#include "board.h"

#include <esp_heap_caps.h>
#include <esp_log.h>
#include <memory>
#include <stdexcept>
#include <string>

#define REMOTE_EMOJI_LOADER_TAG "RemoteEmojiLoader"
#define MAX_REMOTE_EMOJI_BYTES (250 * 1024)

class RemoteEmojiLoader {
public:
    static std::unique_ptr<LvglImage> Load(const std::string& url) {
        ESP_LOGI(REMOTE_EMOJI_LOADER_TAG, "Remote emoji download start: %s", url.c_str());

        auto network = Board::GetInstance().GetNetwork();
        if (network == nullptr) {
            ESP_LOGW(REMOTE_EMOJI_LOADER_TAG, "Network is not available");
            return nullptr;
        }

        auto http = network->CreateHttp(0);
        if (http == nullptr) {
            ESP_LOGW(REMOTE_EMOJI_LOADER_TAG, "Failed to create HTTP client");
            return nullptr;
        }

        if (!http->Open("GET", url)) {
            ESP_LOGW(REMOTE_EMOJI_LOADER_TAG, "Failed to open URL: %s", url.c_str());
            return nullptr;
        }

        if (http->GetStatusCode() != 200) {
            ESP_LOGW(REMOTE_EMOJI_LOADER_TAG, "HTTP status %d for %s", http->GetStatusCode(), url.c_str());
            http->Close();
            return nullptr;
        }

        size_t content_length = http->GetBodyLength();
        ESP_LOGI(REMOTE_EMOJI_LOADER_TAG, "Remote emoji content length: %u", static_cast<unsigned>(content_length));
        if (content_length == 0 || content_length > MAX_REMOTE_EMOJI_BYTES) {
            ESP_LOGW(REMOTE_EMOJI_LOADER_TAG, "Rejected remote emoji size: %u", static_cast<unsigned>(content_length));
            http->Close();
            return nullptr;
        }

        void* data = heap_caps_malloc(content_length, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
        if (data == nullptr) {
            ESP_LOGI(REMOTE_EMOJI_LOADER_TAG, "PSRAM allocation failed, trying internal RAM");
            data = heap_caps_malloc(content_length, MALLOC_CAP_8BIT);
        }
        if (data == nullptr) {
            ESP_LOGW(REMOTE_EMOJI_LOADER_TAG, "Failed to allocate %u bytes", static_cast<unsigned>(content_length));
            http->Close();
            return nullptr;
        }

        size_t total_read = 0;
        auto* out = static_cast<uint8_t*>(data);
        while (total_read < content_length) {
            int ret = http->Read(reinterpret_cast<char*>(out + total_read), content_length - total_read);
            if (ret < 0) {
                ESP_LOGW(REMOTE_EMOJI_LOADER_TAG, "HTTP read failed: %d", ret);
                http->Close();
                heap_caps_free(data);
                return nullptr;
            }
            if (ret == 0) {
                break;
            }
            total_read += static_cast<size_t>(ret);
        }
        http->Close();

        if (total_read != content_length) {
            ESP_LOGW(REMOTE_EMOJI_LOADER_TAG, "Size mismatch: %u/%u", static_cast<unsigned>(total_read), static_cast<unsigned>(content_length));
            heap_caps_free(data);
            return nullptr;
        }

        try {
            auto image = std::make_unique<LvglAllocatedImage>(data, content_length);
            ESP_LOGI(REMOTE_EMOJI_LOADER_TAG, "Remote emoji decoded successfully: %u bytes", static_cast<unsigned>(content_length));
            return image;
        } catch (const std::exception& e) {
            ESP_LOGW(REMOTE_EMOJI_LOADER_TAG, "Decode failed: %s", e.what());
            heap_caps_free(data);
            return nullptr;
        } catch (...) {
            ESP_LOGW(REMOTE_EMOJI_LOADER_TAG, "Decode failed");
            heap_caps_free(data);
            return nullptr;
        }
    }
};

#endif
