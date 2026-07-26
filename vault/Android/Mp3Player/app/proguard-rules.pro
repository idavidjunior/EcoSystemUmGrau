-keepattributes *Annotation*, EnclosingMethod, Signature
-keep class com.mp3player.** { *; }
-keep class com.mp3player.data.** { *; }

# Room
-keep class * extends androidx.room.RoomDatabase
-keep @androidx.room.Entity class *
-dontwarn androidx.room.paging.**

# Media3 / ExoPlayer
-dontwarn androidx.media3.**
-keep class androidx.media3.** { *; }

# Glide
-keep class com.bumptech.glide.** { *; }
-dontwarn com.bumptech.glide.**

# Kotlin Coroutines
-dontwarn kotlinx.coroutines.**
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}

# JAudiotagger
-dontwarn org.jaudiotagger.**
-keep class org.jaudiotagger.** { *; }

# mp3agic
-dontwarn com.mpatric.mp3agic.**
-keep class com.mpatric.mp3agic.** { *; }

# Gson / Serialization
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}
