package com.mp3player

import android.content.Intent
import android.content.SharedPreferences
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.DocumentsContract
import android.provider.Settings
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.fragment.app.Fragment

class SettingsFragment : Fragment() {

    private var totalSongs: Int = 0
    private var totalArtists: Int = 0
    private var totalAlbums: Int = 0
    private var onRescan: (() -> Unit)? = null
    private var prefs: SharedPreferences? = null

    private lateinit var etMinSize: EditText
    private lateinit var etMinDuration: EditText
    private lateinit var etFolderPath: EditText

    private val folderPickerLauncher = registerForActivityResult(
        ActivityResultContracts.OpenDocumentTree()
    ) { uri: Uri? ->
        if (uri != null) {
            val path = convertSafUriToPath(uri)
            if (path != null) {
                etFolderPath.setText(path)
                saveFilterSettings()
                Toast.makeText(requireContext(), "Pasta: $path", Toast.LENGTH_LONG).show()
            } else {
                Toast.makeText(requireContext(), "Não foi possível obter o caminho da pasta", Toast.LENGTH_LONG).show()
            }
        }
    }

    fun setStats(songs: Int, artists: Int, albums: Int) {
        totalSongs = songs
        totalArtists = artists
        totalAlbums = albums
        updateViews()
    }

    fun setOnRescan(callback: () -> Unit) {
        onRescan = callback
    }

    override fun onCreateView(inflater: LayoutInflater, c: ViewGroup?, b: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_settings, c, false)
        prefs = requireContext().getSharedPreferences("mp3player_prefs", 0)

        v.findViewById<View>(R.id.card_library).setOnClickListener { updateViews() }

        v.findViewById<View>(R.id.card_about).setOnClickListener {
            startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.parse("package:${requireContext().packageName}")
            })
        }

        etMinSize = v.findViewById(R.id.et_min_size)
        etMinDuration = v.findViewById(R.id.et_min_duration)
        etFolderPath = v.findViewById(R.id.et_folder_path)
        val btnBrowse = v.findViewById<Button>(R.id.btn_browse_folder)
        val btnRescan = v.findViewById<Button>(R.id.btn_rescan)
        val btnToggleTheme = v.findViewById<Button>(R.id.btn_toggle_theme)

        loadFilterSettings()

        val currentTheme = prefs?.getString("theme", "dark") ?: "dark"
        btnToggleTheme.text = if (currentTheme == "dark") "Alternar para Tema Claro" else "Alternar para Tema Escuro"

        btnToggleTheme.setOnClickListener {
            val newTheme = if (currentTheme == "dark") "light" else "dark"
            prefs?.edit()?.putString("theme", newTheme)?.apply()
            Toast.makeText(requireContext(), "Tema alterado. Reiniciando...", Toast.LENGTH_SHORT).show()
            requireActivity().recreate()
        }

        btnBrowse.setOnClickListener {
            folderPickerLauncher.launch(null)
        }

        btnRescan.setOnClickListener {
            saveFilterSettings()
            Toast.makeText(requireContext(), "Reescanneando biblioteca...", Toast.LENGTH_SHORT).show()
            onRescan?.invoke()
        }

        val tvVersion = v.findViewById<TextView>(R.id.tv_version_name)
        val tvBuild = v.findViewById<TextView>(R.id.tv_build_info)
        val tvDevice = v.findViewById<TextView>(R.id.tv_device_info)
        val tvPerm = v.findViewById<TextView>(R.id.tv_permission_status)

        try {
            val pkg = requireContext().packageManager.getPackageInfo(requireContext().packageName, 0)
            tvVersion.text = "MP3 Player v${pkg.versionName}"
            tvBuild.text = "Build ${pkg.versionCode} · ${BuildConfig.BUILD_DATE}"
        } catch (e: Exception) {
            tvVersion.text = "MP3 Player v1.0.0"
            tvBuild.text = "Build info unavailable"
        }

        tvDevice.text = "${Build.MANUFACTURER} ${Build.MODEL} · Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})"
        tvPerm.text = getPermissionStatusText()
        tvPerm.setTextColor(if (isPermissionGranted()) 0xFF1DB954.toInt() else 0xFFFF4444.toInt())

        updateViews()
        return v
    }

    override fun onPause() {
        super.onPause()
        saveFilterSettings()
    }

    private fun loadFilterSettings() {
        etMinSize.setText(prefs?.getString("min_size_kb", "500") ?: "500")
        etMinDuration.setText(prefs?.getString("min_duration_sec", "30") ?: "30")
        etFolderPath.setText(prefs?.getString("scan_folder", "") ?: "")
    }

    private fun saveFilterSettings() {
        prefs?.edit()?.apply {
            putString("min_size_kb", etMinSize.text.toString())
            putString("min_duration_sec", etMinDuration.text.toString())
            putString("scan_folder", etFolderPath.text.toString())
            apply()
        }
    }

    private fun convertSafUriToPath(uri: Uri): String? {
        return try {
            val docId = DocumentsContract.getTreeDocumentId(uri)
            val colonIdx = docId.indexOf(':')
            if (colonIdx < 0) return null
            val storageId = docId.substring(0, colonIdx)
            val subPath = docId.substring(colonIdx + 1)
            if (storageId == "primary") {
                "/storage/emulated/0/$subPath"
            } else {
                "/storage/$storageId/$subPath"
            }
        } catch (e: Exception) {
            null
        }
    }

    private fun isPermissionGranted(): Boolean {
        val ctx = requireContext()
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            Environment.isExternalStorageManager()
        } else {
            android.content.pm.PackageManager.PERMISSION_GRANTED ==
                androidx.core.content.ContextCompat.checkSelfPermission(
                    ctx, android.Manifest.permission.READ_EXTERNAL_STORAGE
                )
        }
    }

    private fun getPermissionStatusText(): String {
        return if (isPermissionGranted()) "✓ Permissão de armazenamento concedida"
        else "✗ Permissão de armazenamento NÃO concedida"
    }

    private fun updateViews() {
        val v = view ?: return
        v.findViewById<TextView>(R.id.tv_stat_songs).text = "$totalSongs"
        v.findViewById<TextView>(R.id.tv_stat_artists).text = "$totalArtists"
        v.findViewById<TextView>(R.id.tv_stat_albums).text = "$totalAlbums"
    }
}
