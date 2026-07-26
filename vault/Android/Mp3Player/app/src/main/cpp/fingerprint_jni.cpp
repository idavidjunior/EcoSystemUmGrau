#include <jni.h>
#include <string>
#include <vector>
#include <android/log.h>
#include <chromaprint.h>

#define LOG_TAG "Fingerprint"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

extern "C" JNIEXPORT jstring JNICALL
Java_com_mp3player_data_online_AcoustIDService_generateFingerprint(
    JNIEnv *env, jobject /*thiz*/,
    jbyteArray pcm_data,
    jint sample_rate,
    jint num_channels) {

    jsize len = env->GetArrayLength(pcm_data);
    if (len < 256 || sample_rate <= 0 || (num_channels != 1 && num_channels != 2)) {
        LOGE("Invalid parameters: len=%d, rate=%d, channels=%d", len, sample_rate, num_channels);
        return env->NewStringUTF("");
    }

    jbyte *bytes = env->GetByteArrayElements(pcm_data, nullptr);
    if (!bytes) {
        LOGE("Failed to get byte array elements");
        return env->NewStringUTF("");
    }

    int16_t *samples = reinterpret_cast<int16_t *>(bytes);
    int num_samples = len / 2;

    ChromaprintContext *ctx = chromaprint_new(CHROMAPRINT_ALGORITHM_DEFAULT);
    if (!ctx) {
        LOGE("Failed to create Chromaprint context");
        env->ReleaseByteArrayElements(pcm_data, bytes, JNI_ABORT);
        return env->NewStringUTF("");
    }

    int ret = chromaprint_start(ctx, sample_rate, num_channels);
    if (!ret) {
        LOGE("chromaprint_start failed");
        chromaprint_free(ctx);
        env->ReleaseByteArrayElements(pcm_data, bytes, JNI_ABORT);
        return env->NewStringUTF("");
    }

    ret = chromaprint_feed(ctx, samples, num_samples);
    if (!ret) {
        LOGE("chromaprint_feed failed");
        chromaprint_free(ctx);
        env->ReleaseByteArrayElements(pcm_data, bytes, JNI_ABORT);
        return env->NewStringUTF("");
    }

    ret = chromaprint_finish(ctx);
    if (!ret) {
        LOGE("chromaprint_finish failed");
        chromaprint_free(ctx);
        env->ReleaseByteArrayElements(pcm_data, bytes, JNI_ABORT);
        return env->NewStringUTF("");
    }

    char *fingerprint = nullptr;
    ret = chromaprint_get_fingerprint(ctx, &fingerprint);
    if (!ret || !fingerprint) {
        LOGE("chromaprint_get_fingerprint failed");
        chromaprint_free(ctx);
        env->ReleaseByteArrayElements(pcm_data, bytes, JNI_ABORT);
        return env->NewStringUTF("");
    }

    jstring result = env->NewStringUTF(fingerprint);
    chromaprint_dealloc(fingerprint);
    chromaprint_free(ctx);
    env->ReleaseByteArrayElements(pcm_data, bytes, JNI_ABORT);

    LOGI("Fingerprint generated: %s", result ? "success" : "failed");
    return result;
}
