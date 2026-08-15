// Serviço WebSocket para jarvis_bridge:8765
// Reconexão automática, parsing tipado, streams reativos

import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as ws_status;
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
  Completer<void>? _connectCompleter;

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

  /// Inicia conexão (idempotente)
  Future<void> connect() async {
    if (_channel != null && _connectionStatus == ConnectionStatus.connected) return;
    if (_connectCompleter != null) return _connectCompleter!.future;

    _connectCompleter = Completer<void>();
    _disposed = false;
    _scheduleConnect();
    try {
      return await _connectCompleter!.future;
    } catch (e) {
      _connectCompleter = null;
      rethrow;
    }
  }

  void _scheduleConnect() {
    if (_disposed) return;
    _updateConnectionStatus(ConnectionStatus.connecting);
    _connect().catchError((e) {
      if (!_disposed) {
        _reconnectTimer = Timer(reconnectDelay, _scheduleConnect);
      }
    });
  }

  Future<void> _connect() async {
    final uri = Uri.parse('ws://$host:$port/ws');
    try {
      _channel = WebSocketChannel.connect(uri);
      final stream = _channel!.stream;
      stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
        cancelOnError: false,
      );
      _startPing();
      _updateConnectionStatus(ConnectionStatus.connected);
      _connectCompleter?.complete();
      _connectCompleter = null;
      requestState();
    } catch (e) {
      _onError(e);
      _connectCompleter?.completeError(e);
      _connectCompleter = null;
    }
  }

  void _startPing() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(pingInterval, (_) {
      if (_channel != null && _connectionStatus == ConnectionStatus.connected) {
        _send({'type': 'ping', 'timestamp': DateTime.now().toIso8601String()});
        requestState();
      }
    });
  }

  void _onMessage(dynamic message) {
    try {
      final data = jsonDecode(message as String);
      _parseMessage(data);
    } catch (e) {
      _errorController.add('Parse error: $e');
    }
  }

  void _parseMessage(Map<String, dynamic> data) {
    final type = data['type'] as String?;
    switch (type) {
      case 'state':
        final state = EcosystemState.fromJson(data['payload'] ?? {});
        _stateController.add(state);
        break;
      case 'log':
        final log = LogEntry.fromJson(data['payload'] ?? {});
        _logController.add(log);
        break;
      case 'pong':
        // Keep alive response
        break;
      case 'error':
        _errorController.add(data['message'] ?? 'Bridge error');
        break;
      default:
        _errorController.add('Unknown message type: $type');
    }
  }

  void _onError(Object error) {
    if (_disposed) return;
    _errorController.add(error);
    _updateConnectionStatus(ConnectionStatus.error);
    _scheduleReconnect();
  }

  void _onDone() {
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
        _errorController.add('Send error: $e');
      }
    }
  }

  /// Envia comando para o bridge
  void sendCommand(String command, [Map<String, dynamic>? args]) {
    _send({
      'type': 'command',
      'command': command,
      'args': args ?? {},
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  /// Solicita estado completo
  void requestState() {
    _send({'type': 'get_state', 'timestamp': DateTime.now().toIso8601String()});
  }

  /// Fecha conexão
  Future<void> dispose() async {
    _disposed = true;
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    _connectCompleter?.completeError(StateError('Disposed'));
    await _channel?.sink.close(ws_status.normalClosure);
    await _stateController.close();
    await _connectionController.close();
    await _logController.close();
    await _errorController.close();
    _channel = null;
  }
}

enum ConnectionStatus { disconnected, connecting, connected, error }

/// Provider para injeção de dependência (riverpod/provider)
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
    // Connect asynchronously to avoid blocking constructor
    _client.connect().catchError((e) {
      // Connection failed silently, UI will show disconnected status
      debugPrint('Bridge connection failed: $e');
    });
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
    // Log error silently, UI can listen to errorStream if needed
  }

  void requestState() => _client.requestState();
  void sendCommand(String cmd, [Map<String, dynamic>? args]) => _client.sendCommand(cmd, args);

  @override
  void dispose() {
    _client.dispose();
    super.dispose();
  }
}