# Music Player

Projeto Android completo para um reprodutor de música MP3 fluido, com:
- Interface em Jetpack Compose
- Reprodução com ExoPlayer
- Serviço em primeiro plano e notificação de mídia
- Leitura de músicas locais via MediaStore
- Controles de reprodução e seekbar interativo

## Como abrir
1. Abra o Android Studio.
2. Selecione `Open` e escolha a pasta `Reprodutor MP3 VSCODE`.
3. Aguarde a sincronização do Gradle.

## Como gerar o APK
1. No Android Studio, abra `Build > Build Bundle(s) / APK(s) > Build APK(s)`.
2. Após a conclusão, clique em `locate` para abrir a pasta com o APK.
3. Transfira o APK para o seu smartphone ou instale diretamente via `adb install`.

## Requisitos
- Android Studio com SDK Android 34
- Kotlin 1.9
- Projeto configurado para `minSdk 24`

## Permissões
O aplicativo pede permissão de leitura de mídia para acessar músicas MP3 armazenadas no dispositivo.

## Notas
- Sem `gradle` instalado no terminal local, use o Android Studio para abrir o projeto e criar o APK.
- O app funciona melhor com arquivos MP3 internos do dispositivo e suporta reprodução em segundo plano.
