package com.biblia.estudo.ui.resources;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.database.sqlite.SQLiteDatabase;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.view.View;
import android.widget.AdapterView;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.data.ResourceFolderDao;
import com.biblia.estudo.data.UserResourceDao;
import com.biblia.estudo.model.ResourceFolder;
import com.biblia.estudo.model.UserResource;
import com.biblia.estudo.utils.NavigationHelper;

import java.util.List;

public class ResourcesActivity extends Activity {

    private static final int REQUEST_FILE = 2001;
    private static final int REQUEST_FOLDER = 2002;

    private LinearLayout foldersContainer;
    private ListView filesList;
    private TextView emptyText, folderTitle;

    private UserResourceDao resourceDao;
    private ResourceFolderDao folderDao;
    private long currentFolderId = -2; // -2 = all, -1 = uncategorized
    private String currentFolderName = "Todos os arquivos";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_resources);

        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getBibleDatabase();
        resourceDao = new UserResourceDao(db);
        folderDao = new ResourceFolderDao(db);

        foldersContainer = findViewById(R.id.foldersContainer);
        filesList = findViewById(R.id.filesList);
        emptyText = findViewById(R.id.emptyText);
        folderTitle = findViewById(R.id.folderTitle);

        NavigationHelper.setupBackButton(this);

        findViewById(R.id.btnAddFile).setOnClickListener(v -> importFile());
        findViewById(R.id.btnAddFolder).setOnClickListener(v -> showNewFolderDialog());
        refreshFolders();
        refreshFiles();
    }

    private void refreshFolders() {
        foldersContainer.removeAllViews();
        List<ResourceFolder> folders = folderDao.getAll();

        // Uncategorized button
        View uncat = getLayoutInflater().inflate(R.layout.item_resource_folder, foldersContainer, false);
        ((TextView) uncat.findViewById(android.R.id.text1)).setText("\uD83D\uDCE5  Sem pasta");
        int uncatCount = resourceDao.countByFolder(-1);
        ((TextView) uncat.findViewById(android.R.id.text2)).setText(uncatCount + " arquivos");
        uncat.setOnClickListener(v -> showUncategorized());
        uncat.setOnLongClickListener(v -> false);
        foldersContainer.addView(uncat);

        for (ResourceFolder f : folders) {
            View v = getLayoutInflater().inflate(R.layout.item_resource_folder, foldersContainer, false);
            ((TextView) v.findViewById(android.R.id.text1)).setText(f.getIcon() + "  " + f.getName());
            ((TextView) v.findViewById(android.R.id.text2)).setText(f.getItemCount() + " arquivos");

            v.setOnClickListener(click -> {
                currentFolderId = f.getId();
                currentFolderName = f.getName();
                refreshFiles();
            });

            v.setOnLongClickListener(click -> {
                showFolderActions(f);
                return true;
            });

            foldersContainer.addView(v);
        }
    }

    private void refreshFiles() {
        List<UserResource> files;
        if (currentFolderId == -2) {
            files = resourceDao.getAll();
            folderTitle.setText("Todos os arquivos");
        } else if (currentFolderId == -1) {
            files = resourceDao.getByFolder(-1);
            folderTitle.setText("Sem pasta");
        } else {
            files = resourceDao.getByFolder(currentFolderId);
            ResourceFolder f = folderDao.getById(currentFolderId);
            folderTitle.setText(f != null ? (f.getIcon() + "  " + f.getName()) : "Pasta");
        }

        filesList.setAdapter(new com.biblia.estudo.ui.library.ResourceListAdapter(this, files));
        emptyText.setVisibility(files.isEmpty() ? View.VISIBLE : View.GONE);
        if (files.isEmpty()) emptyText.setText("Nenhum arquivo aqui");

        filesList.setAdapter(new com.biblia.estudo.ui.library.ResourceListAdapter(this, files));
        filesList.setOnItemClickListener((parent, view, position, id) -> {
            UserResource res = (UserResource) parent.getItemAtPosition(position);
            try {
                Intent intent = new Intent(Intent.ACTION_VIEW);
                intent.setDataAndType(Uri.parse(res.getUri()), res.getMimeType());
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                startActivity(intent);
            } catch (Exception e) {
                Toast.makeText(this, "Erro ao abrir arquivo", Toast.LENGTH_SHORT).show();
            }
        });
        filesList.setOnItemLongClickListener((parent, view, position, id) -> {
            UserResource res = (UserResource) parent.getItemAtPosition(position);
            showFileActions(res);
            return true;
        });
    }

    private void showAllFiles() {
        currentFolderId = -2;
        currentFolderName = "Todos os arquivos";
        refreshFiles();
    }

    private void showUncategorized() {
        currentFolderId = -1;
        currentFolderName = "Sem pasta";
        refreshFiles();
    }

    private void showFileActions(UserResource res) {
        String[] options = {"Mover para pasta...", "Renomear", "Excluir"};
        new AlertDialog.Builder(this)
                .setTitle(res.getTitle())
                .setItems(options, (dialog, which) -> {
                    if (which == 0) moveFile(res);
                    else if (which == 1) renameFile(res);
                    else {
                        resourceDao.deleteById(res.getId());
                        refreshFiles();
                        refreshFolders();
                        Toast.makeText(this, "Excluído", Toast.LENGTH_SHORT).show();
                    }
                }).show();
    }

    private void moveFile(UserResource res) {
        List<ResourceFolder> folders = folderDao.getAll();
        if (folders.isEmpty()) {
            Toast.makeText(this, "Crie uma pasta primeiro", Toast.LENGTH_SHORT).show();
            return;
        }
        String[] names = new String[folders.size() + 1];
        final long[] ids = new long[folders.size() + 1];
        names[0] = "(Sem pasta)";
        ids[0] = -1;
        for (int i = 0; i < folders.size(); i++) {
            names[i + 1] = folders.get(i).getName();
            ids[i + 1] = folders.get(i).getId();
        }
        new AlertDialog.Builder(this)
                .setTitle("Mover: " + res.getTitle())
                .setItems(names, (dialog, which) -> {
                    resourceDao.moveToFolder(res.getId(), ids[which]);
                    refreshFiles();
                    refreshFolders();
                }).show();
    }

    private void renameFile(UserResource res) {
        EditText input = new EditText(this);
        input.setText(res.getTitle());
        input.setPadding(40, 20, 40, 20);
        new AlertDialog.Builder(this)
                .setTitle("Renomear")
                .setView(input)
                .setPositiveButton("OK", (d, w) -> {
                    String name = input.getText().toString().trim();
                    if (!name.isEmpty()) {
                        com.biblia.estudo.data.UserResourceDao dao = resourceDao;
                        android.content.ContentValues cv = new android.content.ContentValues();
                        cv.put("title", name);
                        dao.getClass(); // access db through method
                        // Use raw query for simplicity
                        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getBibleDatabase();
                        db.execSQL("UPDATE user_resources SET title=? WHERE _id=?",
                                new String[]{name, String.valueOf(res.getId())});
                        refreshFiles();
                        refreshFolders();
                    }
                })
                .setNegativeButton("Cancelar", null)
                .show();
    }

    private void showFolderActions(ResourceFolder f) {
        String[] options = {"Renomear pasta", "Excluir pasta"};
        new AlertDialog.Builder(this)
                .setTitle(f.getName())
                .setItems(options, (dialog, which) -> {
                    if (which == 0) renameFolder(f);
                    else {
                        folderDao.delete(f.getId());
                        refreshFolders();
                        if (currentFolderId == f.getId()) showAllFiles();
                        Toast.makeText(this, "Pasta excluída", Toast.LENGTH_SHORT).show();
                    }
                }).show();
    }

    private void renameFolder(ResourceFolder f) {
        EditText input = new EditText(this);
        input.setText(f.getName());
        input.setPadding(40, 20, 40, 20);
        new AlertDialog.Builder(this)
                .setTitle("Renomear pasta")
                .setView(input)
                .setPositiveButton("OK", (d, w) -> {
                    String name = input.getText().toString().trim();
                    if (!name.isEmpty()) {
                        folderDao.updateName(f.getId(), name);
                        refreshFolders();
                        refreshFiles();
                    }
                })
                .setNegativeButton("Cancelar", null)
                .show();
    }

    private void showNewFolderDialog() {
        EditText input = new EditText(this);
        input.setHint("Nome da pasta");
        input.setPadding(40, 20, 40, 20);
        new AlertDialog.Builder(this)
                .setTitle("Nova pasta")
                .setView(input)
                .setPositiveButton("Criar", (d, w) -> {
                    String name = input.getText().toString().trim();
                    if (!name.isEmpty()) {
                        ResourceFolder f = new ResourceFolder();
                        f.setName(name);
                        f.setIcon("\uD83D\uDCC1");
                        folderDao.insert(f);
                        refreshFolders();
                        Toast.makeText(this, "Pasta criada", Toast.LENGTH_SHORT).show();
                    }
                })
                .setNegativeButton("Cancelar", null)
                .show();
    }

    private void importFile() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        startActivityForResult(intent, REQUEST_FILE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null) return;

        if (requestCode == REQUEST_FILE) {
            Uri uri = data.getData();
            if (uri == null) return;
            try { getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION); } catch (Exception ignored) {}
            addResource(uri);
        } else if (requestCode == REQUEST_FOLDER) {
            Uri treeUri = data.getData();
            if (treeUri == null) return;
            try { getContentResolver().takePersistableUriPermission(treeUri, Intent.FLAG_GRANT_READ_URI_PERMISSION); } catch (Exception ignored) {}
            importFolderContents(treeUri);
        }
    }

    private void addResource(Uri uri) {
        String title = extractFileName(uri);
        String mime = getContentResolver().getType(uri);
        if (mime == null) mime = "application/octet-stream";
        long size = extractFileSize(uri);
        UserResource res = new UserResource();
        res.setTitle(title);
        res.setUri(uri.toString());
        res.setMimeType(mime);
        res.setSize(size);
        res.setFolderId(currentFolderId >= 0 ? currentFolderId : -1);
        res.setCreatedAt(System.currentTimeMillis());
        resourceDao.insert(res);
        refreshFiles();
        refreshFolders();
        Toast.makeText(this, "Importado: " + title, Toast.LENGTH_SHORT).show();
    }

    private void importFolderContents(Uri treeUri) {
        try {
            android.database.Cursor c = getContentResolver().query(
                    android.provider.DocumentsContract.buildChildDocumentsUriUsingTree(treeUri,
                            android.provider.DocumentsContract.getTreeDocumentId(treeUri)),
                    new String[]{
                            android.provider.DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                            android.provider.DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                            android.provider.DocumentsContract.Document.COLUMN_MIME_TYPE,
                            android.provider.DocumentsContract.Document.COLUMN_SIZE},
                    null, null, null);
            if (c != null) {
                int count = 0;
                while (c.moveToNext()) {
                    String mime = c.getString(2);
                    if (mime != null && !mime.contains("vnd.android.document/directory")) {
                        String docId = c.getString(0);
                        Uri childUri = android.provider.DocumentsContract.buildDocumentUriUsingTree(treeUri, docId);
                        String name = c.getString(1);
                        long size = c.getLong(3);
                        UserResource res = new UserResource();
                        res.setTitle(name);
                        res.setUri(childUri.toString());
                        res.setMimeType(mime);
                        res.setSize(size);
                        res.setFolderId(currentFolderId >= 0 ? currentFolderId : -1);
                        res.setCreatedAt(System.currentTimeMillis());
                        resourceDao.insert(res);
                        count++;
                    }
                }
                c.close();
                refreshFiles();
                refreshFolders();
                Toast.makeText(this, count + " arquivos importados", Toast.LENGTH_SHORT).show();
            }
        } catch (Exception e) {
            Toast.makeText(this, "Erro ao importar pasta", Toast.LENGTH_SHORT).show();
        }
    }

    private String extractFileName(Uri uri) {
        String name = "Arquivo";
        try (android.database.Cursor c = getContentResolver().query(uri, null, null, null, null)) {
            if (c != null && c.moveToFirst()) {
                int idx = c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (idx >= 0) name = c.getString(idx);
            }
        } catch (Exception ignored) {}
        if (name == null || name.isEmpty()) name = uri.getLastPathSegment();
        return name != null ? name : "Arquivo";
    }

    private long extractFileSize(Uri uri) {
        long size = 0;
        try (android.database.Cursor c = getContentResolver().query(uri, null, null, null, null)) {
            if (c != null && c.moveToFirst()) {
                int idx = c.getColumnIndex(OpenableColumns.SIZE);
                if (idx >= 0) size = c.getLong(idx);
            }
        } catch (Exception ignored) {}
        return size;
    }
}
