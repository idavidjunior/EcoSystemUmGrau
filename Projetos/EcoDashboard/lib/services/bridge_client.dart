// Serviço WebSocket para jarvis_bridge:8765
// Reconexão automática, parsing tipado, streams reativos

import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../models/ecosystem_state.dart';

class BridgeClient {
  static const String defaultHost = 'localhost';
  static const int defaultPort = 8765;
  static const Duration reconnectDelay = Duration(seconds: 3);
  static const Duration pingInterval = Duration(seconds: 15);

  WebSocketChannel? _channel;
  final String host;
  final int port;
  bool _disposed = false;
  Timer? _reconnectTimer;
  Timer? _pingTimer;
  StreamSubscription? _sub;

  // Streams de saída
  final _stateController = StreamController<EcosystemState>.broadcast();
  final _connectionController = StreamController<ConnectionStatus>.broadcast();
  final _logController = StreamController<LogEntry>.broadcast();
  final _errorController = StreamController<Object>.broadcast();

  Stream<EcosystemState> get stateStream => _stateController.stream;
  Stream<ConnectionStatus> get connectionStream => _connectionController.stream;
  Stream<LogEntry> get logStream => _logController.stream;
  Stream<Object> get errorStream => _errorController.stream;

  ConnectionStatus _connectionStatus = ConnectionStatus.disconnected;
  ConnectionStatus get connectionStatus => _connectionStatus;

  BridgeClient({this.host = defaultHost, this.port = defaultPort});

  void start() {
    _disposed = false;
    _scheduleConnect();
  }

  void _scheduleConnect() {
    if (_disposed) return;
    _updateConnectionStatus(ConnectionStatus.connecting);
    _connect();
  }

  Future<void> _connect() async {
    final uri = Uri.parse('ws://$host:$port');
    debugPrint('[BridgeClient] conectando $uri');
    try {
      _channel = WebSocketChannel.connect(uri);
      // Aguarda handshake completar
      await _channel!.ready;
      debugPrint('[BridgeClient] handshake OK');
      _updateConnectionStatus(ConnectionStatus.connected);

      // Escuta mensagens
      _sub = _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
      );

      _startPing();
      // Pede estado imediatamente
      requestState();
      debugPrint('[BridgeClient] conectado e ouvindo');
    } catch (e) {
      debugPrint('[BridgeClient] connect erro: $e');
      _updateConnectionStatus(ConnectionStatus.error);
      _scheduleReconnect();
    }
  }

  void _startPing() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(pingInterval, (_) {
      if (_channel != null && _connectionStatus == ConnectionStatus.connected) {
        _send({'type': 'ping', 'timestamp': DateTime.now().toIso8601String()});
      }
    });
  }

  void _onMessage(dynamic message) {
    try {
      final data = jsonDecode(message as String);
      _parseMessage(data);
    } catch (e) {
      debugPrint('[BridgeClient] parse error: $e');
    }
  }

  void _parseMessage(Map<String, dynamic> data) {
    final type = data['type'] as String?;
    switch (type) {
      case 'state':
        final payload = (data['payload'] ?? {}) as Map<String, dynamic>;
        try {
          final state = EcosystemState.fromJson(payload);
          _stateController.add(state);
        } catch (e) {
          debugPrint('[BridgeClient] state parse error: $e');
          _errorController.add('State parse error: $e');
        }
        break;
      case 'log':
        try {
          final log = LogEntry.fromJson((data['payload'] ?? {}) as Map<String, dynamic>);
          _logController.add(log);
        } catch (_) {}
        break;
      case 'pong':
        break;
      case 'error':
        _errorController.add(data['message'] ?? 'Bridge error');
        break;
      default:
        break;
    }
  }

  void _onError(Object error) {
    debugPrint('[BridgeClient] onError: $error');
    if (_disposed) return;
    _errorController.add(error);
    _updateConnectionStatus(ConnectionStatus.error);
    _scheduleReconnect();
  }

  void _onDone() {
    debugPrint('[BridgeClient] onDone');
    if (_disposed) return;
    _updateConnectionStatus(ConnectionStatus.disconnected);
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(reconnectDelay, () {
      if (!_disposed) _scheduleConnect();
    });
  }

  void _updateConnectionStatus(ConnectionStatus status) {
    if (_connectionStatus != status) {
      _connectionStatus = status;
      _connectionController.add(status);
    }
  }

  void _send(Map<String, dynamic> message) {
    if (_channel != null && _connectionStatus == ConnectionStatus.connected) {
      try {
        _channel!.sink.add(jsonEncode(message));
      } catch (e) {
        debugPrint('[BridgeClient] send erro: $e');
      }
    }
  }

  void sendCommand(String command, [Map<String, dynamic>? args]) {
    _send({
      'type': 'command',
      'command': command,
      'args': args ?? {},
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  void requestState() {
    _send({'type': 'get_state', 'timestamp': DateTime.now().toIso8601String()});
  }

  void dispose() {
    _disposed = true;
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    _sub?.cancel();
    _channel?.sink.close();
    _stateController.close();
    _connectionController.close();
    _logController.close();
    _errorController.close();
    _channel = null;
  }
}

enum ConnectionStatus { disconnected, connecting, connected, error }

/// Provider para injeção de dependência
class BridgeClientProvider extends ChangeNotifier {
  late final BridgeClient _client;
  BridgeClient get client => _client;
  EcosystemState? _currentState;
  EcosystemState? get currentState => _currentState;
  ConnectionStatus _connectionStatus = ConnectionStatus.disconnected;
  ConnectionStatus get connectionStatus => _connectionStatus;
  final List<LogEntry> _logs = [];
  List<LogEntry> get logs => List.unmodifiable(_logs);

  BridgeClientProvider({String host = 'localhost', int port = 8765}) {
    _client = BridgeClient(host: host, port: port);
    _client.stateStream.listen(_onState);
    _client.connectionStream.listen(_onConnection);
    _client.logStream.listen(_onLog);
    _client.errorStream.listen(_onError);
    _client.start();
  }

  void _onState(EcosystemState state) {
    _currentState = state;
    notifyListeners();
  }

  void _onConnection(ConnectionStatus status) {
    _connectionStatus = status;
    notifyListeners();
  }

  void _onLog(LogEntry log) {
    _logs.insert(0, log);
    if (_logs.length > 500) _logs.removeLast();
    notifyListeners();
  }

  void _onError(Object error) {
    debugPrint('[BridgeProvider] error: $error');
  }

  void requestState() => _client.requestState();
  void sendCommand(String cmd, [Map<String, dynamic>? args]) => _client.sendCommand(cmd, args);

  @override
  void dispose() {
    _client.dispose();
    super.dispose();
  }
}
