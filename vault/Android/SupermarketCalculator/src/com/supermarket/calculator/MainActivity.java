package com.supermarket.calculator;

import com.supermarket.calculator.models.CartItem;
import com.supermarket.calculator.adapter.CartAdapter;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.text.format.DateFormat;
import android.view.inputmethod.EditorInfo;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.animation.AlphaAnimation;
import android.view.animation.Animation;
import android.widget.*;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.FilenameFilter;
import java.io.IOException;
import java.text.NumberFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;

public class MainActivity extends Activity implements CartAdapter.CartListener {

    private AutoCompleteTextView productNameInput;
    private TextView priceDisplay, qtyDisplay, totalDisplay, itemCount;
    private ListView cartList;
    private List<CartItem> items;
    private CartAdapter adapter;
    private int currentQty = 1;
    private StringBuilder priceBuffer = new StringBuilder();
    private NumberFormat currencyFormat;
    private int editingIndex = -1;
    private int unnamedCounter = 0;
    private double budgetLimit = 0;
    private boolean budgetWarned = false;
    private boolean budgetExceededWarned = false;
    private Vibrator vibrator;
    private TextView budgetLimitDisplay, budgetRemaining;
    private android.os.Handler budgetBlinkHandler;
    private boolean budgetBlinkVisible = true;

    // Tabs
    private LinearLayout calculatorPage, savedListsPage;
    private ScrollView settingsPage;
    private TextView tabCalculator, tabSavedLists, tabSettings;

    // Saved files cache
    private List<File> savedFiles = new ArrayList<>();
    private java.util.Map<String, String> savedListTitles = new java.util.HashMap<>();
    private java.util.Map<String, String> expFinanceTitles = new java.util.HashMap<>();

    // Listas sub-tabs
    private LinearLayout expFinanceFilesContent;
    private ListView expReportsListView;
    private TextView emptyExpReportsText;
    private List<File> expFinanceFiles = new ArrayList<>();
    private BaseAdapter expFinanceAdapter;

    // Grocery items
    private ArrayList<String> allGroceryItems = new ArrayList<>();
    private ArrayAdapter<String> groceryAdapter;

    // Settings
    private SharedPreferences prefs;
    private static final String PREFS_NAME = "settings";
    private static final String KEY_THEME = "theme";
    private static final String KEY_SKIN = "skin";
    private static final String KEY_SHOW_OPS = "show_ops";
    private static final String KEY_SHOW_BACK = "show_back";
    private static final String KEY_SHOW_CLEAR = "show_clear";
    private static final String KEY_SHOW_00 = "show_00";
    private static final String KEY_CUSTOM_ITEMS = "custom_grocery_items";
    private static final int THEME_DEFAULT = 0;
    private static final int THEME_DARK = 1;
    private static final int THEME_BLUE = 2;
    private static final int SKIN_DEFAULT = 0;
    private static final int SKIN_ROUNDED = 1;

    private int currentTheme = THEME_DEFAULT;
    private int currentSkin = SKIN_DEFAULT;
    private boolean showOps = false, showBack = true, showClear = true, show00 = true;

    private LinearLayout opsRow;
    private double operand1 = 0;
    private String pendingOp = null;

    private Button btnNBack, btnNClear, btnN00;
    private LinearLayout rootLayout, headerBar, tabBar, numpadContainer;

    // Expenses tab
    private TextView tabExpenses;
    private LinearLayout expensesPage;
    private EditText expenseDesc, expenseAmount;
    private Button expenseCategoryBtn;
    private boolean[] selectedCategoryStates;
    private String selectedCategorySummary = "";
    private Button addExpenseBtn, expenseReportBtn, expenseExportBtn, expenseClearBtn;
    private ListView expenseListView;
    private TextView emptyExpensesText, expenseTotalDisplay, expensePaidDisplay, expenseRemainingDisplay;
    private ArrayList<ExpenseItem> expenseItems = new ArrayList<>();
    private BaseAdapter expenseAdapter;
    private String[] expenseCategories;
    private ArrayList<String> customCategories = new ArrayList<>();
    private int editingExpensePosition = -1;
    private boolean expensePaidMode = false;
    private Button btnConcluirPaid;

    // Listas sub-tab views (shared names from original expenses sub-tabs)
    private TextView expTabMarket, expTabFinance;
    private LinearLayout expMarketContent, expFinanceContent;
    private ListView expMarketListView;
    private TextView expMarketEmptyText;
    private List<File> marketListFiles = new ArrayList<>();
    private View marketSelectionBar;
    private TextView marketSelectionCount;
    private EditText marketAmountInput;
    private Button marketApplyBtn, marketCancelBtn;
    private boolean marketSelectionMode = false;
    private Set<Integer> selectedMarketIndices = new HashSet<>();
    private BaseAdapter marketAdapter;

    // Finance budget
    private double financeBudgetLimit = 0;
    private static final String KEY_PAID_FILES = "paid_expense_files";
    private Set<String> paidFiles = new HashSet<>();
    private LinearLayout expFinanceSummaryRow;
    private TextView expFinanceTotalValue, expFinancePaidValue, expFinanceRemainingValue, expFinanceBudgetDisplay;
    private File currentExpenseFile = null;
    private TextView financeBudgetLimitDisplay, financeBudgetRemaining;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Log.d("SuperCalc", "onCreate called");

        prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        loadSettings();
        loadCustomGroceryItems();

        vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        currencyFormat = NumberFormat.getCurrencyInstance(new Locale("pt", "BR"));

        initViews();
        setupTabs();
        setupCalculator();
        setupNumpad();
        setupListasSubTabs();
        setupExpenses();
        setupSettings();

        applyTheme();
        applySkin();
        applyNumpadCustomization();

        updatePriceDisplay();
        updateTotal();
        refreshSavedLists();
    }

    private void initViews() {
        rootLayout = findViewById(R.id.rootLayout);
        headerBar = findViewById(R.id.headerBar);
        tabBar = findViewById(R.id.tabBar);

        productNameInput = findViewById(R.id.productNameInput);
        priceDisplay = findViewById(R.id.priceDisplay);
        qtyDisplay = findViewById(R.id.qtyDisplay);
        totalDisplay = findViewById(R.id.totalDisplay);
        itemCount = findViewById(R.id.itemCount);
        cartList = findViewById(R.id.cartList);
        budgetLimitDisplay = findViewById(R.id.budgetLimitDisplay);
        budgetRemaining = findViewById(R.id.budgetRemaining);

        calculatorPage = findViewById(R.id.calculatorPage);
        savedListsPage = findViewById(R.id.savedListsPage);
        settingsPage = findViewById(R.id.settingsPage);

        tabCalculator = findViewById(R.id.tabCalculator);
        tabSavedLists = findViewById(R.id.tabSavedLists);
        tabSettings = findViewById(R.id.tabSettings);

        opsRow = findViewById(R.id.opsRow);
        btnNBack = findViewById(R.id.btnNBack);
        btnNClear = findViewById(R.id.btnNClear);
        btnN00 = findViewById(R.id.btnN00);
        numpadContainer = findViewById(R.id.numpadContainer);

        tabExpenses = findViewById(R.id.tabExpenses);
        expensesPage = findViewById(R.id.expensesPage);
        expenseDesc = findViewById(R.id.expenseDesc);
        expenseAmount = findViewById(R.id.expenseAmount);
        expenseCategoryBtn = findViewById(R.id.expenseCategoryBtn);
        addExpenseBtn = findViewById(R.id.addExpenseBtn);
        expenseReportBtn = findViewById(R.id.expenseReportBtn);
        expenseExportBtn = findViewById(R.id.expenseExportBtn);
        expenseClearBtn = findViewById(R.id.expenseClearBtn);
        expenseListView = findViewById(R.id.expenseListView);
        emptyExpensesText = findViewById(R.id.emptyExpensesText);
        expenseTotalDisplay = findViewById(R.id.expenseTotalDisplay);
        expensePaidDisplay = findViewById(R.id.expensePaidDisplay);
        expenseRemainingDisplay = findViewById(R.id.expenseRemainingDisplay);
        btnConcluirPaid = findViewById(R.id.btnConcluirPaid);
        btnConcluirPaid.setOnClickListener(v -> exitExpensePaidMode());

        financeBudgetLimitDisplay = findViewById(R.id.financeBudgetLimitDisplay);
        financeBudgetRemaining = findViewById(R.id.financeBudgetRemaining);
        financeBudgetLimit = prefs.getFloat("finance_budget_limit", 0f);
        findViewById(R.id.financeBudgetRow).setOnClickListener(v -> showFinanceBudgetDialog());

        expTabMarket = findViewById(R.id.expTabMarket);
        expTabFinance = findViewById(R.id.expTabFinance);
        expMarketContent = findViewById(R.id.expMarketContent);
        expFinanceContent = findViewById(R.id.expFinanceContent);
        expMarketListView = findViewById(R.id.expMarketListView);
        expMarketEmptyText = findViewById(R.id.expMarketEmptyText);
        marketSelectionBar = findViewById(R.id.marketSelectionBar);
        marketSelectionCount = findViewById(R.id.marketSelectionCount);
        marketAmountInput = findViewById(R.id.marketAmountInput);
        marketApplyBtn = findViewById(R.id.marketApplyBtn);
        marketCancelBtn = findViewById(R.id.marketCancelBtn);
        expFinanceFilesContent = findViewById(R.id.expFinanceFilesContent);
        expReportsListView = findViewById(R.id.expReportsListView);
        emptyExpReportsText = findViewById(R.id.emptyExpReportsText);
        expFinanceSummaryRow = findViewById(R.id.expFinanceSummaryRow);
        expFinanceTotalValue = findViewById(R.id.expFinanceTotalValue);
        expFinancePaidValue = findViewById(R.id.expFinancePaidValue);
        expFinanceRemainingValue = findViewById(R.id.expFinanceRemainingValue);
        expFinanceBudgetDisplay = findViewById(R.id.expFinanceBudgetDisplay);
    }

    private void loadSettings() {
        currentTheme = prefs.getInt(KEY_THEME, THEME_DEFAULT);
        currentSkin = prefs.getInt(KEY_SKIN, SKIN_DEFAULT);
        showOps = prefs.getBoolean(KEY_SHOW_OPS, false);
        showBack = prefs.getBoolean(KEY_SHOW_BACK, true);
        showClear = prefs.getBoolean(KEY_SHOW_CLEAR, true);
        show00 = prefs.getBoolean(KEY_SHOW_00, true);
    }

    private void saveSettings() {
        prefs.edit()
            .putInt(KEY_THEME, currentTheme)
            .putInt(KEY_SKIN, currentSkin)
            .putBoolean(KEY_SHOW_OPS, showOps)
            .putBoolean(KEY_SHOW_BACK, showBack)
            .putBoolean(KEY_SHOW_CLEAR, showClear)
            .putBoolean(KEY_SHOW_00, show00)
            .apply();
    }

    private void setupTabs() {
        tabCalculator.setOnClickListener(v -> switchTab(0));
        tabExpenses.setOnClickListener(v -> switchTab(1));
        tabSavedLists.setOnClickListener(v -> switchTab(2));
        tabSettings.setOnClickListener(v -> switchTab(3));
        switchTab(0);
    }

    private void switchTab(int index) {
        calculatorPage.setVisibility(index == 0 ? View.VISIBLE : View.GONE);
        expensesPage.setVisibility(index == 1 ? View.VISIBLE : View.GONE);
        savedListsPage.setVisibility(index == 2 ? View.VISIBLE : View.GONE);
        settingsPage.setVisibility(index == 3 ? View.VISIBLE : View.GONE);

        tabCalculator.setAlpha(index == 0 ? 1f : 0.6f);
        tabExpenses.setAlpha(index == 1 ? 1f : 0.6f);
        tabSavedLists.setAlpha(index == 2 ? 1f : 0.6f);
        tabSettings.setAlpha(index == 3 ? 1f : 0.6f);

        tabCalculator.setBackgroundResource(index == 0 ? R.drawable.bg_tab_active : 0);
        tabExpenses.setBackgroundResource(index == 1 ? R.drawable.bg_tab_active : 0);
        tabSavedLists.setBackgroundResource(index == 2 ? R.drawable.bg_tab_active : 0);
        tabSettings.setBackgroundResource(index == 3 ? R.drawable.bg_tab_active : 0);

        if (index == 1) {
            refreshExpensesMarket();
            refreshFinanceFiles();
        }
        if (index == 2) {
            refreshExpenseTotal();
        }
        if (expensePaidMode) exitExpensePaidMode();
    }

    // ==================== CALCULATOR ====================

    private void setupCalculator() {
        items = new ArrayList<>();
        adapter = new CartAdapter(this, items, this);
        cartList.setAdapter(adapter);

        findViewById(R.id.budgetRow).setOnClickListener(v -> showBudgetLimitDialog());

        rebuildGroceryAdapter();

        findViewById(R.id.btnGroceryDropdown).setOnClickListener(v -> {
            showGroceryListSelection();
        });

        findViewById(R.id.incQtyBtn).setOnClickListener(v -> {
            currentQty = Math.min(999, currentQty + 1);
            qtyDisplay.setText(String.valueOf(currentQty));
        });
        findViewById(R.id.decQtyBtn).setOnClickListener(v -> {
            if (currentQty > 1) {
                currentQty--;
                qtyDisplay.setText(String.valueOf(currentQty));
            }
        });
        findViewById(R.id.addButton).setOnClickListener(v -> addOrUpdateItem());
        findViewById(R.id.finishButton).setOnClickListener(v -> finishPurchase());
        findViewById(R.id.clearButton).setOnClickListener(v -> clearCart());
    }

    private void showGroceryListSelection() {
        String[] rawItems = allGroceryItems.toArray(new String[0]);
        String[] displayItems = new String[rawItems.length + 1];
        boolean[] inCart = new boolean[rawItems.length + 1];
        java.util.Set<String> cartNames = new java.util.HashSet<>();
        for (CartItem ci : items) {
            cartNames.add(ci.getName().toLowerCase(Locale.ROOT));
        }
        for (int i = 0; i < rawItems.length; i++) {
            boolean already = cartNames.contains(rawItems[i].toLowerCase(Locale.ROOT));
            inCart[i] = already;
            displayItems[i] = already ? "\u2705 " + rawItems[i] : rawItems[i];
        }
        displayItems[rawItems.length] = "\u2795 Personalizar...";
        inCart[rawItems.length] = false;

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Lista de Produtos");
        builder.setItems(displayItems, (dialog, which) -> {
            if (which == rawItems.length) {
                showAddCustomItemDialog();
                return;
            }
            String name = rawItems[which];
            productNameInput.setText(name);
            productNameInput.setSelection(name.length());
            productNameInput.requestFocus();
        });
        builder.setNeutralButton("Adicionar todos", (dialog, which) -> {
            for (String name : allGroceryItems) {
                CartItem newItem = new CartItem(name, 0, 1);
                mergeOrAddAtTop(newItem);
            }
            adapter.notifyDataSetChanged();
            updateTotal();
            Toast.makeText(this, "Lista completa adicionada! Preencha os pre\u00e7os um por um.", Toast.LENGTH_LONG).show();
        });
        builder.setNegativeButton("Fechar", null);
        builder.show();
    }

    private void showAddCustomItemDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Adicionar item personalizado");
        EditText input = new EditText(this);
        input.setHint("Nome do produto");
        input.setPadding(40, 20, 40, 20);
        builder.setView(input);
        builder.setPositiveButton("Adicionar", (dialog, which) -> {
            String name = input.getText().toString().trim();
            if (!name.isEmpty()) {
                saveCustomGroceryItem(name);
                showGroceryListSelection();
            }
        });
        builder.setNegativeButton("Cancelar", null);
        builder.show();
    }

    // ==================== GROCERY ITEMS PERSISTENCE ====================

    private void loadCustomGroceryItems() {
        String json = prefs.getString(KEY_CUSTOM_ITEMS, "[]");
        try {
            JSONArray arr = new JSONArray(json);
            for (int i = 0; i < arr.length(); i++) {
                allGroceryItems.add(arr.getString(i));
            }
        } catch (Exception e) {
            Log.e("SuperCalc", "Error loading custom items", e);
        }
    }

    private void saveCustomGroceryItem(String name) {
        if (name == null || name.trim().isEmpty()) return;
        String trimmed = name.trim();
        for (String item : allGroceryItems) {
            if (item.equalsIgnoreCase(trimmed)) return;
        }
        allGroceryItems.add(trimmed);
        Collections.sort(allGroceryItems, String.CASE_INSENSITIVE_ORDER);
        try {
            JSONArray arr = new JSONArray();
            for (String item : allGroceryItems) {
                arr.put(item);
            }
            prefs.edit().putString(KEY_CUSTOM_ITEMS, arr.toString()).apply();
        } catch (Exception e) {
            Log.e("SuperCalc", "Error saving custom items", e);
        }
        rebuildGroceryAdapter();
        Toast.makeText(this, trimmed + " " + getString(R.string.custom_saved), Toast.LENGTH_SHORT).show();
    }

    private void rebuildGroceryAdapter() {
        String[] defaults = getResources().getStringArray(R.array.grocery_items);
        ArrayList<String> merged = new ArrayList<>();
        Collections.addAll(merged, defaults);
        for (String custom : allGroceryItems) {
            boolean found = false;
            for (String def : defaults) {
                if (def.equalsIgnoreCase(custom)) { found = true; break; }
            }
            if (!found) merged.add(custom);
        }
        Collections.sort(merged, String.CASE_INSENSITIVE_ORDER);
        allGroceryItems.clear();
        allGroceryItems.addAll(merged);
        groceryAdapter = new ArrayAdapter<>(this,
                android.R.layout.simple_dropdown_item_1line, allGroceryItems);
        productNameInput.setAdapter(groceryAdapter);
        productNameInput.setDropDownWidth(ViewGroup.LayoutParams.MATCH_PARENT);
    }

    // ==================== NUMPAD ====================

    private void setupNumpad() {
        View.OnClickListener numpadListener = v -> {
            String val = null;
            int id = v.getId();
            if (id == R.id.btnN0) val = "0";
            else if (id == R.id.btnN1) val = "1";
            else if (id == R.id.btnN2) val = "2";
            else if (id == R.id.btnN3) val = "3";
            else if (id == R.id.btnN4) val = "4";
            else if (id == R.id.btnN5) val = "5";
            else if (id == R.id.btnN6) val = "6";
            else if (id == R.id.btnN7) val = "7";
            else if (id == R.id.btnN8) val = "8";
            else if (id == R.id.btnN9) val = "9";
            else if (id == R.id.btnN00) val = "00";
            else if (id == R.id.btnNComma) val = ",";
            else if (id == R.id.btnNBack) val = "⌫";
            else if (id == R.id.btnNClear) val = "C";

            if (val != null) handleNumpadInput(val);
        };

        int[] numpadIds = {
            R.id.btnN0, R.id.btnN1, R.id.btnN2, R.id.btnN3, R.id.btnN4,
            R.id.btnN5, R.id.btnN6, R.id.btnN7, R.id.btnN8, R.id.btnN9,
            R.id.btnN00, R.id.btnNComma, R.id.btnNBack, R.id.btnNClear
        };

        for (int id : numpadIds) {
            findViewById(id).setOnClickListener(numpadListener);
        }

        findViewById(R.id.btnOpAdd).setOnClickListener(v -> handleOperator("+"));
        findViewById(R.id.btnOpSub).setOnClickListener(v -> handleOperator("−"));
        findViewById(R.id.btnOpMul).setOnClickListener(v -> handleOperator("×"));
        findViewById(R.id.btnOpDiv).setOnClickListener(v -> handleOperator("÷"));
        findViewById(R.id.btnOpEq).setOnClickListener(v -> handleEquals());
    }

    private void handleNumpadInput(String val) {
        if (val.equals("⌫")) {
            if (pendingOp != null && priceBuffer.length() == 0) {
                pendingOp = null;
                updatePriceDisplay();
                return;
            }
            if (priceBuffer.length() > 0) {
                priceBuffer.deleteCharAt(priceBuffer.length() - 1);
            }
        } else if (val.equals("C")) {
            priceBuffer.setLength(0);
            operand1 = 0;
            pendingOp = null;
        } else if (val.equals(",")) {
            if (priceBuffer.indexOf(",") == -1) {
                priceBuffer.append(",");
            }
        } else {
            String beforeComma = priceBuffer.indexOf(",") >= 0
                ? priceBuffer.substring(0, priceBuffer.indexOf(","))
                : priceBuffer.toString();
            if (priceBuffer.indexOf(",") >= 0) {
                String afterComma = priceBuffer.substring(priceBuffer.indexOf(",") + 1);
                if (afterComma.length() < 2) {
                    priceBuffer.append(val);
                }
            } else if (beforeComma.length() < 8) {
                priceBuffer.append(val);
            }
        }
        updatePriceDisplay();
    }

    private void handleOperator(String op) {
        if (pendingOp != null) {
            double current = getPriceFromDisplay();
            operand1 = evaluate(operand1, current, pendingOp);
        } else {
            operand1 = getPriceFromDisplay();
        }
        priceBuffer.setLength(0);
        pendingOp = op;
        updatePriceDisplay();
    }

    private void handleEquals() {
        if (pendingOp == null) return;
        double current = getPriceFromDisplay();
        operand1 = evaluate(operand1, current, pendingOp);
        pendingOp = null;
        priceBuffer.setLength(0);
        priceBuffer.append(String.format(Locale.US, "%.2f", operand1).replace(".", ","));
        updatePriceDisplay();
    }

    private double evaluate(double a, double b, String op) {
        switch (op) {
            case "+": return a + b;
            case "−": return a - b;
            case "×": return a * b;
            case "÷": return (b != 0) ? a / b : 0;
            default: return b;
        }
    }

    private void updatePriceDisplay() {
        if (pendingOp != null && priceBuffer.length() == 0) {
            priceDisplay.setText(currencyFormat.format(operand1) + " " + pendingOp);
            priceDisplay.setTextColor(getColorForCurrentTheme(true));
            return;
        }
        if (priceBuffer.length() == 0) {
            priceDisplay.setText("R$ 0,00");
            priceDisplay.setTextColor(getColorForCurrentTheme(true));
            return;
        }
        try {
            double value = Double.parseDouble(priceBuffer.toString().replace(",", "."));
            priceDisplay.setText(currencyFormat.format(value));
            priceDisplay.setTextColor(getColorForCurrentTheme(true));
        } catch (NumberFormatException e) {
            priceDisplay.setText("R$ 0,00");
            priceDisplay.setTextColor(getColorForCurrentTheme(true));
        }
    }

    private double getPriceFromDisplay() {
        if (priceBuffer.length() == 0) return 0;
        try {
            return Double.parseDouble(priceBuffer.toString().replace(",", "."));
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    // ==================== ITEM MANAGEMENT ====================

    private void addOrUpdateItem() {
        String name = productNameInput.getText().toString().trim();
        double price = getPriceFromDisplay();

        if (price <= 0) {
            Toast.makeText(this, "Informe um preço válido.", Toast.LENGTH_SHORT).show();
            return;
        }

        if (editingIndex >= 0 && editingIndex < items.size()) {
            CartItem edited = items.remove(editingIndex);
            edited.setUnitPrice(price);
            edited.setQuantity(currentQty);
            mergeOrAddAtTop(edited);
            editingIndex = -1;
        } else {
            if (name.isEmpty()) {
                unnamedCounter++;
                name = "Item " + unnamedCounter;
                CartItem newItem = new CartItem(name, price, currentQty);
                items.add(0, newItem);
            } else {
                CartItem newItem = new CartItem(name, price, currentQty);
                mergeOrAddAtTop(newItem);
                saveCustomGroceryItem(name);
            }
        }

        adapter.notifyDataSetChanged();
        updateTotal();
        resetInput();
    }

    private void mergeOrAddAtTop(CartItem newItem) {
        for (int i = 0; i < items.size(); i++) {
            if (items.get(i).getName().equalsIgnoreCase(newItem.getName())) {
                CartItem existing = items.remove(i);
                existing.setQuantity(existing.getQuantity() + newItem.getQuantity());
                items.add(0, existing);
                return;
            }
        }
        items.add(0, newItem);
    }

    private void loadItemForEditing(int position) {
        if (position < 0 || position >= items.size()) return;
        CartItem item = items.get(position);
        productNameInput.setText(item.getName());
        priceBuffer.setLength(0);
        priceBuffer.append(String.format(Locale.US, "%.2f", item.getUnitPrice()).replace(".", ","));
        updatePriceDisplay();
        currentQty = item.getQuantity();
        qtyDisplay.setText(String.valueOf(currentQty));
        editingIndex = position;
        adapter.setEditingPosition(position);
    }

    private void resetInput() {
        productNameInput.setText("");
        priceBuffer.setLength(0);
        operand1 = 0;
        pendingOp = null;
        currentQty = 1;
        qtyDisplay.setText("1");
        editingIndex = -1;
        adapter.setEditingPosition(-1);
        updatePriceDisplay();
    }

    private void updateTotal() {
        double total = 0;
        int count = 0;
        for (CartItem item : items) {
            total += item.getTotal();
            count += item.getQuantity();
        }
        totalDisplay.setText(currencyFormat.format(total));
        itemCount.setText(count + " " + (count == 1 ? "item" : "itens"));
        checkBudgetWarning(total);
        updateBudgetDisplay(total);
    }

    private void checkBudgetWarning(double currentTotal) {
        if (budgetLimit <= 0) return;
        double pct = (currentTotal / budgetLimit) * 100;

        if (pct >= 100) {
            if (!budgetExceededWarned) {
                vibrateStrong();
                Toast.makeText(this, R.string.budget_exceeded, Toast.LENGTH_LONG).show();
                budgetExceededWarned = true;
            }
        } else if (pct >= 80) {
            if (!budgetWarned) {
                vibrateStrong();
                Toast.makeText(this, R.string.budget_approaching, Toast.LENGTH_LONG).show();
                budgetWarned = true;
            }
            budgetExceededWarned = false;
        } else {
            budgetWarned = false;
            budgetExceededWarned = false;
        }
    }

    private void vibrateStrong() {
        if (vibrator == null || !vibrator.hasVibrator()) return;
        long[] pattern = {0, 400, 100, 400};
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createWaveform(pattern, -1));
        } else {
            vibrator.vibrate(pattern, -1);
        }
    }

    private void updateBudgetDisplay(double currentTotal) {
        if (budgetLimit <= 0) {
            budgetLimitDisplay.setText(R.string.budget_click_hint);
            budgetRemaining.setText("");
            startBudgetBlink();
            return;
        }
        stopBudgetBlink();
        budgetLimitDisplay.setText(currencyFormat.format(budgetLimit));
        double remaining = budgetLimit - currentTotal;
        if (remaining >= 0) {
            budgetRemaining.setText("Restante: " + currencyFormat.format(remaining));
            budgetRemaining.setTextColor(getColorForCurrentTheme(false));
        } else {
            budgetRemaining.setText("Restante: " + currencyFormat.format(remaining));
            budgetRemaining.setTextColor(getResources().getColor(R.color.budgetWarning));
        }
    }

    private void startBudgetBlink() {
        if (budgetBlinkHandler != null) return;
        budgetBlinkHandler = new android.os.Handler();
        budgetBlinkVisible = true;
        budgetBlinkHandler.post(new Runnable() {
            @Override
            public void run() {
                budgetBlinkVisible = !budgetBlinkVisible;
                float alpha = budgetBlinkVisible ? 1f : 0.3f;
                if (budgetLimit <= 0) {
                    budgetLimitDisplay.setAlpha(alpha);
                    LinearLayout row = findViewById(R.id.budgetRow);
                    if (row != null) row.setAlpha(alpha);
                } else {
                    budgetLimitDisplay.setAlpha(1f);
                    LinearLayout row = findViewById(R.id.budgetRow);
                    if (row != null) row.setAlpha(1f);
                }
                if (financeBudgetLimit <= 0) {
                    LinearLayout fRow = findViewById(R.id.financeBudgetRow);
                    if (fRow != null) fRow.setAlpha(alpha);
                } else {
                    LinearLayout fRow = findViewById(R.id.financeBudgetRow);
                    if (fRow != null) fRow.setAlpha(1f);
                }
                if (budgetLimit > 0 && financeBudgetLimit > 0) {
                    stopBudgetBlink();
                    return;
                }
                if (budgetBlinkHandler != null) {
                    budgetBlinkHandler.postDelayed(this, 500);
                }
            }
        });
    }

    private void stopBudgetBlink() {
        if (budgetBlinkHandler != null) {
            budgetBlinkHandler.removeCallbacksAndMessages(null);
            budgetBlinkHandler = null;
        }
        budgetLimitDisplay.setAlpha(1f);
        LinearLayout row = findViewById(R.id.budgetRow);
        if (row != null) row.setAlpha(1f);
        LinearLayout fRow = findViewById(R.id.financeBudgetRow);
        if (fRow != null) fRow.setAlpha(1f);
    }

    // ==================== BUDGET ====================

    private void showBudgetLimitDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(R.string.budget_dialog_title);

        EditText input = new EditText(this);
        input.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        input.setHint("0,00");
        input.setPadding(40, 20, 40, 20);
        if (budgetLimit > 0) {
            input.setText(String.format(Locale.US, "%.2f", budgetLimit).replace(".", ","));
            input.selectAll();
        }

        builder.setView(input);
        builder.setPositiveButton("OK", (dialog, which) -> {
            String val = input.getText().toString().trim().replace(",", ".");
            try {
                budgetLimit = Double.parseDouble(val);
                if (budgetLimit < 0) budgetLimit = 0;
                budgetWarned = false;
                budgetExceededWarned = false;
            } catch (NumberFormatException e) {
                Toast.makeText(this, "Valor inválido.", Toast.LENGTH_SHORT).show();
                return;
            }
            updateTotal();
        });

        if (budgetLimit > 0) {
            builder.setNeutralButton(R.string.budget_dialog_clear, (dialog, which) -> {
                budgetLimit = 0;
                budgetWarned = false;
                budgetExceededWarned = false;
                updateTotal();
            });
        }

        builder.setNegativeButton("Cancelar", null);
        builder.show();
    }

    private void showFinanceBudgetDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(R.string.budget_dialog_title);

        EditText input = new EditText(this);
        input.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        input.setHint("0,00");
        input.setPadding(40, 20, 40, 20);
        if (financeBudgetLimit > 0) {
            input.setText(String.format(Locale.US, "%.2f", financeBudgetLimit).replace(".", ","));
            input.selectAll();
        }

        builder.setView(input);
        builder.setPositiveButton("OK", (dialog, which) -> {
            String val = input.getText().toString().trim().replace(",", ".");
            try {
                financeBudgetLimit = Double.parseDouble(val);
                if (financeBudgetLimit < 0) financeBudgetLimit = 0;
                prefs.edit().putFloat("finance_budget_limit", (float) financeBudgetLimit).apply();
            } catch (NumberFormatException e) {
                Toast.makeText(this, "Valor inválido.", Toast.LENGTH_SHORT).show();
                return;
            }
            refreshExpenseTotal();
        });

        if (financeBudgetLimit > 0) {
            builder.setNeutralButton(R.string.budget_dialog_clear, (dialog, which) -> {
                financeBudgetLimit = 0;
                prefs.edit().remove("finance_budget_limit").apply();
                refreshExpenseTotal();
            });
        }

        builder.setNegativeButton("Cancelar", null);
        builder.show();
    }

    private void clearCart() {
        if (items.isEmpty()) return;
        new AlertDialog.Builder(this)
            .setTitle("Limpar carrinho")
            .setMessage("Tem certeza que deseja remover todos os itens?")
            .setPositiveButton("Sim", (dialog, which) -> {
                items.clear();
                unnamedCounter = 0;
                budgetWarned = false;
                budgetExceededWarned = false;
                adapter.notifyDataSetChanged();
                updateTotal();
                resetInput();
            })
            .setNegativeButton("Cancelar", null)
            .show();
    }

    private void finishPurchase() {
        if (items.isEmpty()) {
            Toast.makeText(this, "Carrinho vazio!", Toast.LENGTH_SHORT).show();
            return;
        }

        double total = 0;
        StringBuilder receipt = new StringBuilder();
        receipt.append(getString(R.string.receipt_title)).append("\n");
        receipt.append(new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault()).format(new Date())).append("\n\n");

        for (CartItem item : items) {
            String line = String.format(Locale.US, "%s x%d %s = %s",
                item.getName(),
                item.getQuantity(),
                currencyFormat.format(item.getUnitPrice()),
                currencyFormat.format(item.getTotal()));
            receipt.append(line).append("\n");
            total += item.getTotal();
        }

        receipt.append("\n");
        for (int i = 0; i < 22; i++) receipt.append("─");
        receipt.append("\n");
        receipt.append("TOTAL: ").append(currencyFormat.format(total));
        receipt.append("\n");
        for (int i = 0; i < 22; i++) receipt.append("─");

        String receiptContent = receipt.toString();

        LinearLayout finishLayout = new LinearLayout(this);
        finishLayout.setOrientation(LinearLayout.VERTICAL);
        finishLayout.setPadding(40, 0, 40, 0);

        ScrollView receiptScroll = new ScrollView(this);
        receiptScroll.setLayoutParams(new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        TextView receiptView = new TextView(this);
        receiptView.setText(receiptContent);
        receiptView.setTextSize(12f);
        receiptView.setTypeface(android.graphics.Typeface.MONOSPACE);
        receiptView.setTextColor(getResources().getColor(R.color.textPrimary));
        receiptScroll.addView(receiptView);

        LinearLayout btnRow = new LinearLayout(this);
        btnRow.setOrientation(LinearLayout.HORIZONTAL);
        btnRow.setLayoutParams(new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        btnRow.setPadding(0, 16, 0, 0);

        Button btnSaveList = new Button(this);
        btnSaveList.setText("Salvar");
        btnSaveList.setLayoutParams(new LinearLayout.LayoutParams(0,
            ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        btnSaveList.setTextSize(12f);

        Button btnSaveModel = new Button(this);
        btnSaveModel.setText("Modelo");
        btnSaveModel.setLayoutParams(new LinearLayout.LayoutParams(0,
            ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        btnSaveModel.setTextSize(12f);

        Button btnSaveExpense = new Button(this);
        btnSaveExpense.setText("Despesa");
        btnSaveExpense.setLayoutParams(new LinearLayout.LayoutParams(0,
            ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        btnSaveExpense.setTextSize(12f);

        Button btnOk = new Button(this);
        btnOk.setText("OK");
        btnOk.setLayoutParams(new LinearLayout.LayoutParams(0,
            ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        btnOk.setTextSize(12f);

        btnRow.addView(btnSaveList);
        btnRow.addView(btnSaveModel);
        btnRow.addView(btnSaveExpense);
        btnRow.addView(btnOk);

        finishLayout.addView(receiptScroll);
        finishLayout.addView(btnRow);

        AlertDialog finishDialog = new AlertDialog.Builder(this)
            .setTitle(R.string.finish_title)
            .setView(finishLayout)
            .setCancelable(false)
            .create();

        btnSaveList.setOnClickListener(v -> {
            finishDialog.dismiss();
            showSaveTitleDialog(receiptContent, "lista_compras");
        });
        btnSaveModel.setOnClickListener(v -> {
            finishDialog.dismiss();
            showSaveTitleDialog(receiptContent, "modelo");
        });
        btnSaveExpense.setOnClickListener(v -> {
            finishDialog.dismiss();
            saveCartAsExpense();
            clearCartAfterFinish();
        });
        btnOk.setOnClickListener(v -> {
            finishDialog.dismiss();
            clearCartAfterFinish();
        });

        finishDialog.show();
    }

    private void showSaveTitleDialog(String receiptContent, String prefix) {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(R.string.save_title_dialog);

        EditText input = new EditText(this);
        input.setHint(R.string.save_title_hint);
        String defaultTitle = prefix.equals("modelo")
            ? "Modelo - " + new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault()).format(new Date())
            : getString(R.string.save_title_default) + " - " + new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault()).format(new Date());
        input.setText(defaultTitle);
        input.selectAll();
        input.setPadding(40, 20, 40, 20);

        builder.setView(input);
        builder.setPositiveButton("Salvar", (d, which) -> {
            String title = input.getText().toString().trim();
            if (title.isEmpty()) title = defaultTitle;
            if (prefix.equals("modelo")) {
                saveStructuredList("modelo", title);
            } else {
                saveListToFile(receiptContent);
                saveStructuredList(prefix, title);
            }
            clearCartAfterFinish();
        });
        builder.setNegativeButton("Cancelar", null);
        builder.show();
    }

    private void clearCartAfterFinish() {
        items.clear();
        unnamedCounter = 0;
        budgetWarned = false;
        budgetExceededWarned = false;
        adapter.notifyDataSetChanged();
        updateTotal();
        resetInput();
    }

    private void saveCartAsExpense() {
        double total = 0;
        StringBuilder desc = new StringBuilder();
        desc.append("Compra de mercado - ");
        for (CartItem item : items) {
            total += item.getTotal();
            if (desc.length() < 100) {
                if (desc.length() > 20) desc.append(", ");
                desc.append(item.getName()).append(" x").append(item.getQuantity());
            }
        }
        expenseItems.add(0, new ExpenseItem(desc.toString(), total, "Compras"));
        saveExpensesToFile();
        expenseAdapter.notifyDataSetChanged();
        refreshExpenseTotal();
        refreshSavedLists();
        Toast.makeText(this, "Adicionado às Despesas Financeiras", Toast.LENGTH_LONG).show();
    }

    private void saveListToFile(String content) {
        File dir = getListasDir();

        String timestamp = new SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", Locale.getDefault()).format(new Date());
        File file = new File(dir, "lista_compras_" + timestamp + ".txt");

        try {
            FileOutputStream fos = new FileOutputStream(file);
            fos.write(content.getBytes("UTF-8"));
            fos.close();
            Toast.makeText(this, getString(R.string.save_success), Toast.LENGTH_LONG).show();
        } catch (IOException e) {
            Toast.makeText(this, R.string.save_error, Toast.LENGTH_SHORT).show();
        }
        refreshSavedLists();
    }

    // ==================== STRUCTURED JSON SAVE/LOAD ====================

    private void saveStructuredList(String prefix, String title) {
        File dir = getListasDir();

        String timestamp = new SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", Locale.getDefault()).format(new Date());
        try {
            JSONObject root = new JSONObject();
            root.put("date", timestamp);
            root.put("prefix", prefix);
            root.put("title", title);

            double total = 0;
            JSONArray itemsArr = new JSONArray();
            for (CartItem item : items) {
                JSONObject obj = new JSONObject();
                obj.put("name", item.getName());
                obj.put("unitPrice", item.getUnitPrice());
                obj.put("quantity", item.getQuantity());
                obj.put("total", item.getTotal());
                itemsArr.put(obj);
                total += item.getTotal();
            }
            root.put("items", itemsArr);
            root.put("total", total);

            File file = new File(dir, prefix + "_" + timestamp + ".json");
            FileWriter fw = new FileWriter(file);
            fw.write(root.toString(2));
            fw.close();

            if (prefix.equals("modelo")) {
                Toast.makeText(this, R.string.template_saved, Toast.LENGTH_LONG).show();
            }
            refreshSavedLists();
        } catch (Exception e) {
            Toast.makeText(this, R.string.save_error, Toast.LENGTH_SHORT).show();
            Log.e("SuperCalc", "Error saving structured list", e);
        }
    }

    private void loadStructuredListIntoCart(File f) {
        try {
            BufferedReader br = new BufferedReader(new FileReader(f));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line);
            }
            br.close();

            JSONObject root = new JSONObject(sb.toString());
            JSONArray itemsArr = root.getJSONArray("items");

            for (int i = 0; i < itemsArr.length(); i++) {
                JSONObject obj = itemsArr.getJSONObject(i);
                String name = obj.getString("name");
                double price = obj.getDouble("unitPrice");
                int qty = obj.getInt("quantity");
                CartItem citem = new CartItem(name, price, qty);
                mergeOrAddAtTop(citem);
            }

            adapter.notifyDataSetChanged();
            updateTotal();
            Toast.makeText(this, R.string.template_loaded, Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "Erro ao carregar lista.", Toast.LENGTH_SHORT).show();
            Log.e("SuperCalc", "Error loading structured list", e);
        }
    }

    private void shareReceipt(String content) {
        Intent intent = new Intent(Intent.ACTION_SEND);
        intent.setType("text/plain");
        intent.putExtra(Intent.EXTRA_TEXT, content);
        startActivity(Intent.createChooser(intent, "Compartilhar lista de compras"));
    }

    // ==================== SAVED LISTS (TXT + JSON) ====================

    private void setupListasSubTabs() {
        // Market list adapter (Compras de Mercado)
        marketAdapter = new BaseAdapter() {
            @Override public int getCount() { return marketListFiles.size(); }
            @Override public Object getItem(int i) { return marketListFiles.get(i); }
            @Override public long getItemId(int i) { return i; }

            @Override
            public View getView(int i, View v, ViewGroup p) {
                if (v == null) {
                    v = LayoutInflater.from(MainActivity.this)
                        .inflate(R.layout.saved_list_item, p, false);
                }
                File f = marketListFiles.get(i);
                String fileName = f.getName();
                TextView nameTv = v.findViewById(R.id.savedItemName);
                TextView dateTv = v.findViewById(R.id.savedItemDate);
                CheckBox checkBox = v.findViewById(R.id.savedItemCheck);
                ImageButton loadBtn = v.findViewById(R.id.savedItemLoad);
                ImageButton shareBtn = v.findViewById(R.id.savedItemShare);
                ImageButton deleteBtn = v.findViewById(R.id.savedItemDelete);

                String title = savedListTitles.get(fileName);
                nameTv.setText(title != null ? title : fileName);
                long lastMod = f.lastModified();
                dateTv.setText(new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault()).format(new Date(lastMod)));

                boolean isSelected = selectedMarketIndices.contains(i);
                if (marketSelectionMode) {
                    checkBox.setVisibility(View.VISIBLE);
                    checkBox.setChecked(isSelected);
                    loadBtn.setVisibility(View.GONE);
                    shareBtn.setVisibility(View.GONE);
                    deleteBtn.setVisibility(View.GONE);
                    nameTv.setTextColor(getResources().getColor(R.color.textPrimary));
                    v.setBackgroundColor(isSelected ? getResources().getColor(R.color.bluePrimary) : 0);
                    if (isSelected) nameTv.setTextColor(getResources().getColor(R.color.white));
                } else {
                    checkBox.setVisibility(View.GONE);
                    loadBtn.setVisibility(View.VISIBLE);
                    shareBtn.setVisibility(View.VISIBLE);
                    deleteBtn.setVisibility(View.VISIBLE);
                    v.setBackgroundColor(0);
                    nameTv.setTextColor(getResources().getColor(R.color.textPrimary));
                }

                v.setOnClickListener(view -> {
                    if (marketSelectionMode) {
                        if (selectedMarketIndices.contains(i)) {
                            selectedMarketIndices.remove(i);
                        } else {
                            selectedMarketIndices.add(i);
                        }
                        updateMarketSelectionBar();
                        marketAdapter.notifyDataSetChanged();
                    } else {
                        showSavedFileContent(f);
                    }
                });
                v.setLongClickable(true);
                v.setOnLongClickListener(view -> {
                    enterMarketSelectionMode(i);
                    return true;
                });
                loadBtn.setOnClickListener(view -> {
                    loadStructuredListIntoCart(f);
                    switchTab(0);
                });
                shareBtn.setOnClickListener(view -> shareSavedFile(f));
                deleteBtn.setOnClickListener(view -> deleteSavedFile(f));
                return v;
            }
        };
        expMarketListView.setAdapter(marketAdapter);

        // Market selection bar buttons
        marketApplyBtn.setOnClickListener(v -> applyMarketSelection());
        marketCancelBtn.setOnClickListener(v -> exitMarketSelectionMode());

        // Expense files adapter (Despesas Financeiras)
        expFinanceAdapter = new BaseAdapter() {
            @Override public int getCount() { return expFinanceFiles.size(); }
            @Override public Object getItem(int i) { return expFinanceFiles.get(i); }
            @Override public long getItemId(int i) { return i; }

            @Override
            public View getView(int i, View v, ViewGroup p) {
                if (v == null) {
                    v = LayoutInflater.from(MainActivity.this)
                        .inflate(R.layout.saved_list_item, p, false);
                }
                File f = expFinanceFiles.get(i);
                String fileName = f.getName();
                TextView nameTv = v.findViewById(R.id.savedItemName);
                TextView dateTv = v.findViewById(R.id.savedItemDate);
                ImageButton loadBtn = v.findViewById(R.id.savedItemLoad);
                CheckBox checkBox = v.findViewById(R.id.savedItemCheck);
                ImageButton shareBtn = v.findViewById(R.id.savedItemShare);
                ImageButton deleteBtn = v.findViewById(R.id.savedItemDelete);

                String title = expFinanceTitles.get(fileName);
                nameTv.setText(title != null ? title : fileName);
                long lastMod = f.lastModified();
                dateTv.setText(new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault()).format(new Date(lastMod)));

                checkBox.setVisibility(View.VISIBLE);
                checkBox.setClickable(true);
                checkBox.setFocusable(true);
                checkBox.setChecked(paidFiles.contains(fileName));
                checkBox.setOnClickListener(view -> {
                    if (paidFiles.contains(fileName)) {
                        paidFiles.remove(fileName);
                    } else {
                        paidFiles.add(fileName);
                    }
                    savePaidFiles();
                    updateFinanceSummary();
                });

                loadBtn.setOnClickListener(view -> {
                    loadExpensesFromFile(f);
                    switchTab(2);
                });
                shareBtn.setOnClickListener(view -> shareSavedFile(f));
                deleteBtn.setOnClickListener(view -> {
                    new AlertDialog.Builder(MainActivity.this)
                        .setTitle("Excluir")
                        .setMessage("Tem certeza que deseja excluir \"" + fileName + "\"?")
                        .setPositiveButton("Sim", (d, w) -> {
                            f.delete();
                            refreshFinanceFiles();
                        })
                        .setNegativeButton("Cancelar", null)
                        .show();
                });
                v.setOnClickListener(view -> showSavedFileContent(f));
                return v;
            }
        };
        expReportsListView.setAdapter(expFinanceAdapter);

        // Listas sub-tab switching
        expTabMarket.setOnClickListener(v -> switchListasSubTab(0));
        expTabFinance.setOnClickListener(v -> switchListasSubTab(1));
        switchListasSubTab(0);
    }

    private void refreshFinanceFiles() {
        expFinanceFiles.clear();
        expFinanceTitles.clear();
        File dir = getListasDir();
        if (dir.exists()) {
            File[] files = dir.listFiles((d, name) ->
                (name.equals("despesas.json") || name.startsWith("despesas_")) && name.endsWith(".json"));
            if (files != null) {
                expFinanceFiles.addAll(Arrays.asList(files));
                Collections.sort(expFinanceFiles, (a, b) -> Long.compare(b.lastModified(), a.lastModified()));
            }
        }
        for (File f : expFinanceFiles) {
            if (f.getName().endsWith(".json")) {
                String title = extractTitleFromJson(f);
                expFinanceTitles.put(f.getName(), title);
            }
        }
        loadPaidFiles();
        expFinanceAdapter.notifyDataSetChanged();
        boolean empty = expFinanceFiles.isEmpty();
        expReportsListView.setVisibility(empty ? View.GONE : View.VISIBLE);
        emptyExpReportsText.setVisibility(empty ? View.VISIBLE : View.GONE);
        updateFinanceSummary();
    }

    private void loadPaidFiles() {
        paidFiles.clear();
        String json = prefs.getString(KEY_PAID_FILES, "[]");
        try {
            JSONArray arr = new JSONArray(json);
            for (int i = 0; i < arr.length(); i++) {
                paidFiles.add(arr.getString(i));
            }
        } catch (Exception e) {
            paidFiles.clear();
        }
    }

    private void savePaidFiles() {
        JSONArray arr = new JSONArray();
        for (String name : paidFiles) {
            arr.put(name);
        }
        prefs.edit().putString(KEY_PAID_FILES, arr.toString()).apply();
    }

    private double getExpenseFileTotal(File f) {
        if (!f.getName().endsWith(".json")) return 0;
        try {
            BufferedReader br = new BufferedReader(new FileReader(f));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
            br.close();
            JSONObject root = new JSONObject(sb.toString());
            JSONArray expenses = root.getJSONArray("expenses");
            double total = 0;
            for (int i = 0; i < expenses.length(); i++) {
                total += expenses.getJSONObject(i).getDouble("amount");
            }
            return total;
        } catch (Exception e) {
            return 0;
        }
    }

    private void updateFinanceSummary() {
        double totalAll = 0;
        double totalPaid = 0;
        for (File f : expFinanceFiles) {
            double ft = getExpenseFileTotal(f);
            totalAll += ft;
            if (paidFiles.contains(f.getName())) {
                totalPaid += ft;
            }
        }
        expFinanceTotalValue.setText(currencyFormat.format(totalAll));
        expFinancePaidValue.setText("Total Pago: " + currencyFormat.format(totalPaid));
        double remaining = totalAll - totalPaid;
        expFinanceRemainingValue.setText("Restante: " + currencyFormat.format(remaining));
        expFinanceRemainingValue.setTextColor(remaining >= 0 ? getResources().getColor(R.color.budgetDefault) : getResources().getColor(R.color.budgetWarning));
        if (financeBudgetLimit > 0) {
            expFinanceBudgetDisplay.setText(currencyFormat.format(financeBudgetLimit));
        } else {
            expFinanceBudgetDisplay.setText(R.string.budget_set);
        }
    }

    private void refreshSavedLists() {
        savedFiles.clear();
        savedListTitles.clear();
        File dir = getListasDir();
        if (dir.exists()) {
            File[] files = dir.listFiles((d, name) ->
                (name.startsWith("lista_compras_") || name.startsWith("modelo_"))
                && (name.endsWith(".txt") || name.endsWith(".json")));
            if (files != null) {
                savedFiles.addAll(Arrays.asList(files));
            }
        }
        Collections.sort(savedFiles, (a, b) -> Long.compare(b.lastModified(), a.lastModified()));
        for (File f : savedFiles) {
            if (f.getName().endsWith(".json")) {
                String title = extractTitleFromJson(f);
                savedListTitles.put(f.getName(), title);
            }
        }
    }

    private String extractTitleFromJson(File f) {
        try {
            BufferedReader br = new BufferedReader(new FileReader(f));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
            br.close();
            JSONObject root = new JSONObject(sb.toString());
            if (root.has("title")) {
                String t = root.getString("title").trim();
                if (!t.isEmpty()) return t;
            }
        } catch (Exception e) {
            // fallback
        }
        return null;
    }

    private void showSavedFileContent(File f) {
        if (f.getName().endsWith(".json")) {
            try {
                BufferedReader br = new BufferedReader(new FileReader(f));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) sb.append(line);
                br.close();

                JSONObject root = new JSONObject(sb.toString());
                StringBuilder display = new StringBuilder();
                if (root.has("title")) {
                    String t = root.getString("title").trim();
                    if (!t.isEmpty()) display.append(t).append("\n");
                }
                if (root.has("expenses")) {
                    JSONArray expArr = root.getJSONArray("expenses");
                    for (int i = 0; i < expArr.length(); i++) {
                        JSONObject obj = expArr.getJSONObject(i);
                        display.append(obj.optString("description", ""))
                            .append(" [").append(obj.optString("category", ""))
                            .append("]: ").append(currencyFormat.format(obj.getDouble("amount")))
                            .append("\n");
                    }
                } else {
                    if (root.has("date")) display.append("Data: ").append(root.getString("date")).append("\n\n");
                    JSONArray itemsArr = root.getJSONArray("items");
                    for (int i = 0; i < itemsArr.length(); i++) {
                        JSONObject obj = itemsArr.getJSONObject(i);
                        display.append(obj.getString("name"))
                            .append(" x").append(obj.getInt("quantity"))
                            .append(" ").append(currencyFormat.format(obj.getDouble("unitPrice")))
                            .append(" = ").append(currencyFormat.format(obj.getDouble("total")))
                            .append("\n");
                    }
                    display.append("\nTOTAL: ").append(currencyFormat.format(root.getDouble("total")));
                }

                String dialogTitle = f.getName();
                String cachedTitle = savedListTitles.get(f.getName());
                if (cachedTitle == null) cachedTitle = expFinanceTitles.get(f.getName());
                if (cachedTitle != null) dialogTitle = cachedTitle;
                AlertDialog.Builder builder = new AlertDialog.Builder(this);
                builder.setTitle(dialogTitle);
                builder.setMessage(display.toString().trim());

                final String finalCachedTitle = cachedTitle;
                builder.setPositiveButton("Editar", (d, w) -> {
                    if (root.has("expenses")) {
                        loadExpensesFromFile(f);
                        switchTab(2);
                    } else {
                        loadStructuredListIntoCart(f);
                        switchTab(0);
                    }
                });
                builder.setNeutralButton(R.string.rename_list, (d, w) -> {
                    showRenameDialog(f, finalCachedTitle);
                });
                builder.setNegativeButton(R.string.ok, null);
                builder.show();
            } catch (Exception e) {
                Toast.makeText(this, "Erro ao ler arquivo.", Toast.LENGTH_SHORT).show();
            }
        } else {
            try {
                BufferedReader br = new BufferedReader(new FileReader(f));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    sb.append(line).append("\n");
                }
                br.close();
                new AlertDialog.Builder(this)
                    .setTitle(f.getName())
                    .setMessage(sb.toString().trim())
                    .setPositiveButton(R.string.ok, null)
                    .show();
            } catch (IOException e) {
                Toast.makeText(this, "Erro ao ler arquivo.", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private void showRenameDialog(File f, String currentTitle) {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(R.string.rename_dialog_title);

        EditText input = new EditText(this);
        input.setHint(R.string.new_title_hint);
        if (currentTitle != null) {
            input.setText(currentTitle);
            input.selectAll();
        }
        input.setPadding(40, 20, 40, 20);
        builder.setView(input);

        builder.setPositiveButton("Salvar", (d, w) -> {
            String newTitle = input.getText().toString().trim();
            if (newTitle.isEmpty()) return;
            updateJsonTitle(f, newTitle);
            refreshSavedLists();
            Toast.makeText(this, "Título atualizado!", Toast.LENGTH_SHORT).show();
        });
        builder.setNegativeButton("Cancelar", null);
        builder.show();
    }

    private void updateJsonTitle(File f, String newTitle) {
        try {
            BufferedReader br = new BufferedReader(new FileReader(f));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
            br.close();

            JSONObject root = new JSONObject(sb.toString());
            root.put("title", newTitle);

            FileWriter fw = new FileWriter(f);
            fw.write(root.toString(2));
            fw.close();
        } catch (Exception e) {
            Toast.makeText(this, "Erro ao renomear.", Toast.LENGTH_SHORT).show();
            Log.e("SuperCalc", "Error renaming", e);
        }
    }

    private void shareSavedFile(File f) {
        try {
            BufferedReader br = new BufferedReader(new FileReader(f));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line).append("\n");
            }
            br.close();
            shareReceipt(sb.toString().trim());
        } catch (IOException e) {
            Toast.makeText(this, "Erro ao ler arquivo.", Toast.LENGTH_SHORT).show();
        }
    }

    private void deleteSavedFile(File f) {
        new AlertDialog.Builder(this)
            .setTitle("Excluir lista")
            .setMessage("Tem certeza que deseja excluir \"" + f.getName() + "\"?")
            .setPositiveButton("Sim", (d, w) -> {
                f.delete();
                refreshSavedLists();
                refreshExpensesMarket();
            })
            .setNegativeButton("Cancelar", null)
            .show();
    }

    // ==================== EXPENSES ====================

    private static class ExpenseItem {
        String description;
        double amount;
        String category;
        long date;
        boolean paid;

        ExpenseItem(String description, double amount, String category) {
            this.description = description;
            this.amount = amount;
            this.category = category;
            this.date = System.currentTimeMillis();
            this.paid = false;
        }
    }

    private void setupExpenses() {
        loadCustomCategories();
        expenseCategories = getAllCategories();

        selectedCategoryStates = new boolean[expenseCategories.length];
        expenseCategoryBtn.setOnClickListener(v -> showCategorySelector());
        expenseCategoryBtn.setLongClickable(false);
        expenseCategoryBtn.setOnLongClickListener(null);

        addExpenseBtn.setOnClickListener(v -> showCategorySelector());

        expenseAdapter = new BaseAdapter() {
            @Override public int getCount() { return expenseItems.size(); }
            @Override public Object getItem(int i) { return expenseItems.get(i); }
            @Override public long getItemId(int i) { return i; }

            @Override
            public View getView(int i, View v, ViewGroup p) {
                if (v == null) {
                    v = LayoutInflater.from(MainActivity.this)
                        .inflate(R.layout.cart_item, p, false);
                }
                ExpenseItem e = expenseItems.get(i);

                EditText nameEt = v.findViewById(R.id.itemName);
                View qtyContainer = v.findViewById(R.id.qtyContainer);
                TextView unitTv = v.findViewById(R.id.itemUnitPrice);
                TextView totalTv = v.findViewById(R.id.itemTotalPrice);
                ImageButton removeBtn = v.findViewById(R.id.removeBtn);
                CheckBox paidCheck = v.findViewById(R.id.itemPaidCheck);
                TextView paidStatus = v.findViewById(R.id.itemPaidStatus);

                qtyContainer.setVisibility(View.GONE);

                if (e.paid) {
                    paidStatus.setVisibility(View.VISIBLE);
                    paidStatus.setText("Pago");
                    paidStatus.setTextColor(Color.parseColor("#2E7D32"));
                    paidStatus.setBackgroundResource(R.drawable.bg_pago_badge);
                } else {
                    paidStatus.setVisibility(View.VISIBLE);
                    paidStatus.setText("Pendente");
                    paidStatus.setTextColor(Color.parseColor("#E65100"));
                    paidStatus.setBackgroundResource(R.drawable.bg_pendente_badge);
                }

                paidCheck.setVisibility(expensePaidMode ? View.VISIBLE : View.GONE);
                paidCheck.setChecked(e.paid);
                paidCheck.setOnClickListener(view -> {
                    e.paid = paidCheck.isChecked();
                    expenseAdapter.notifyDataSetChanged();
                    refreshExpenseTotal();
                    saveExpensesToFile();
                });

                boolean isEditing = i == editingExpensePosition;

                if (isEditing) {
                    nameEt.setFocusable(true);
                    nameEt.setFocusableInTouchMode(true);
                    nameEt.setCursorVisible(true);
                    nameEt.setBackgroundResource(R.drawable.bg_input);
                    nameEt.setPadding(4, 0, 4, 0);
                    nameEt.setTextColor(getResources().getColor(R.color.textPrimary));
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                        v.setBackgroundColor(getColor(R.color.highlightBg));
                    } else {
                        v.setBackgroundColor(getResources().getColor(R.color.highlightBg));
                    }
                } else {
                    nameEt.setFocusable(false);
                    nameEt.setFocusableInTouchMode(false);
                    nameEt.setCursorVisible(false);
                    nameEt.setBackgroundResource(0);
                    nameEt.setPadding(0, 0, 0, 0);
                    nameEt.setTextColor(getResources().getColor(R.color.textPrimary));
                    if (e.paid) {
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                            v.setBackgroundColor(getColor(R.color.paidHighlight));
                        } else {
                            v.setBackgroundColor(getResources().getColor(R.color.paidHighlight));
                        }
                    } else {
                        int colorRes = i % 2 == 0 ? R.color.rowEven : R.color.rowOdd;
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                            v.setBackgroundColor(getColor(colorRes));
                        } else {
                            v.setBackgroundColor(getResources().getColor(colorRes));
                        }
                    }
                }

                Object tag = nameEt.getTag();
                if (tag instanceof TextWatcher) nameEt.removeTextChangedListener((TextWatcher) tag);

                nameEt.setText(e.description);

                TextWatcher watcher = new TextWatcher() {
                    final int pos = i;
                    @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
                    @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}
                    @Override
                    public void afterTextChanged(Editable s) {
                        if (pos == editingExpensePosition) {
                            expenseItems.get(pos).description = s.toString();
                            saveExpensesToFile();
                        }
                    }
                };
                nameEt.addTextChangedListener(watcher);
                nameEt.setTag(watcher);

                unitTv.setText(e.category);
                unitTv.setTextColor(getResources().getColor(R.color.textSecondary));
                totalTv.setTextColor(getResources().getColor(R.color.totalColor));
                unitTv.setTextSize(11f);
                totalTv.setText(currencyFormat.format(e.amount));

                removeBtn.setOnClickListener(ev -> {
                    new AlertDialog.Builder(MainActivity.this)
                        .setTitle(R.string.exp_delete_confirm)
                        .setMessage(e.description + ": " + currencyFormat.format(e.amount))
                        .setPositiveButton("Sim", (d, w) -> {
                            expenseItems.remove(i);
                            editingExpensePosition = -1;
                            expenseAdapter.notifyDataSetChanged();
                            refreshExpenseTotal();
                            saveExpensesToFile();
                        })
                        .setNegativeButton("Cancelar", null)
                        .show();
                });

                final int pos = i;
                v.setOnClickListener(ev -> {
                    if (editingExpensePosition == pos) {
                        editingExpensePosition = -1;
                    } else {
                        editingExpensePosition = pos;
                    }
                    expenseAdapter.notifyDataSetChanged();
                });
                v.setOnLongClickListener(ev -> {
                    if (expensePaidMode) {
                        exitExpensePaidMode();
                    } else {
                        enterExpensePaidMode();
                    }
                    return true;
                });

                totalTv.setOnClickListener(ev -> {
                    EditText input = new EditText(MainActivity.this);
                    input.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
                    input.setText(String.valueOf(e.amount).replace(".", ","));
                    input.setSelectAllOnFocus(true);
                    input.setPadding(40, 20, 40, 20);
                    new AlertDialog.Builder(MainActivity.this)
                        .setTitle("Editar valor: " + e.description)
                        .setView(input)
                        .setPositiveButton("OK", (d, w) -> {
                            String amtStr = input.getText().toString().trim().replace(",", ".");
                            try {
                                double amt = Double.parseDouble(amtStr);
                                if (amt >= 0) {
                                    expenseItems.get(pos).amount = amt;
                                    expenseAdapter.notifyDataSetChanged();
                                    refreshExpenseTotal();
                                    saveExpensesToFile();
                                }
                            } catch (NumberFormatException ignored) {}
                        })
                        .setNegativeButton("Cancelar", null)
                        .show();
                });

                unitTv.setOnClickListener(ev -> {
                    expenseCategories = getAllCategories();
                    final Set<String> selected = new HashSet<>();
                    selected.add(e.category);
                    ArrayAdapter<String> catAdapter = new ArrayAdapter<String>(MainActivity.this,
                            android.R.layout.simple_list_item_1, expenseCategories) {
                        @Override
                        public View getView(int position, View convertView, ViewGroup parent) {
                            View view = super.getView(position, convertView, parent);
                            TextView tv = (TextView) view.findViewById(android.R.id.text1);
                            if (selected.contains(expenseCategories[position])) {
                                view.setBackgroundColor(0xFFDDDDDD);
                            } else {
                                view.setBackgroundColor(Color.WHITE);
                            }
                            tv.setTextColor(Color.BLACK);
                            return view;
                        }
                    };
                    new AlertDialog.Builder(MainActivity.this)
                        .setTitle("Editar categoria")
                        .setAdapter(catAdapter, (d, which) -> {
                            expenseItems.get(pos).category = expenseCategories[which];
                            expenseAdapter.notifyDataSetChanged();
                            saveExpensesToFile();
                        })
                        .setNegativeButton("Cancelar", null)
                        .show();
                });
                return v;
            }
        };
        expenseListView.setAdapter(expenseAdapter);

        expenseReportBtn.setOnClickListener(v -> showExpenseReport());
        expenseExportBtn.setOnClickListener(v -> showSaveExpenseDialog());
        expenseClearBtn.setOnClickListener(v -> clearAllExpenses());

    }

    private void enterMarketSelectionMode(int index) {
        marketSelectionMode = true;
        selectedMarketIndices.add(index);
        marketSelectionBar.setVisibility(View.VISIBLE);
        marketAmountInput.setText("");
        updateMarketSelectionBar();
        marketAdapter.notifyDataSetChanged();
    }

    private void updateMarketSelectionBar() {
        int count = selectedMarketIndices.size();
        marketSelectionCount.setText(count + " selecionada" + (count != 1 ? "s" : ""));
    }

    private void exitMarketSelectionMode() {
        marketSelectionMode = false;
        selectedMarketIndices.clear();
        marketSelectionBar.setVisibility(View.GONE);
        marketAmountInput.setText("");
        marketAdapter.notifyDataSetChanged();
    }

    private void applyMarketSelection() {
        String amtStr = marketAmountInput.getText().toString().trim().replace(",", ".");
        if (amtStr.isEmpty() || selectedMarketIndices.isEmpty()) return;
        double amt;
        try {
            amt = Double.parseDouble(amtStr);
            if (amt < 0) throw new NumberFormatException();
        } catch (NumberFormatException e) {
            Toast.makeText(this, R.string.exp_invalid, Toast.LENGTH_SHORT).show();
            return;
        }
        ArrayList<String> names = new ArrayList<>();
        for (int idx : selectedMarketIndices) {
            File f = marketListFiles.get(idx);
            String title = savedListTitles.get(f.getName());
            names.add(title != null ? title : f.getName());
        }
        String desc = TextUtils.join(", ", names);
        String cat = getString(R.string.exp_cat_other);
        expenseItems.add(0, new ExpenseItem(desc, amt, cat));
        expenseAdapter.notifyDataSetChanged();
        refreshExpenseTotal();
        saveExpensesToFile();
        Toast.makeText(this, "Despesa adicionada: " + currencyFormat.format(amt), Toast.LENGTH_SHORT).show();
        exitMarketSelectionMode();
    }

    private void addExpenseWithCategory(String category) {
        String desc = expenseDesc.getText().toString().trim();
        String amtStr = expenseAmount.getText().toString().trim().replace(",", ".");
        if (amtStr.isEmpty()) {
            Toast.makeText(this, R.string.exp_invalid, Toast.LENGTH_SHORT).show();
            return;
        }
        double amt;
        try {
            amt = Double.parseDouble(amtStr);
            if (amt < 0) throw new NumberFormatException();
        } catch (NumberFormatException e) {
            Toast.makeText(this, R.string.exp_invalid, Toast.LENGTH_SHORT).show();
            return;
        }
        if (desc.isEmpty()) desc = category;
        expenseItems.add(0, new ExpenseItem(desc, amt, category));
        expenseAdapter.notifyDataSetChanged();
        expenseDesc.setText("");
        expenseAmount.setText("");
        selectedCategoryStates = new boolean[expenseCategories.length];
        expenseCategoryBtn.setText("Categorias");
        refreshExpenseTotal();
        saveExpensesToFile();
    }

    private void addExpense() {
        String otherCat = getString(R.string.exp_cat_other);
        addExpenseWithCategory(otherCat);
    }

    private void showCategorySelector() {
        expenseCategories = getAllCategories();
        final boolean[] isMultiSelect = {false};
        final Set<String> selectedItems = new HashSet<>();
        final String ADD_NEW = "+ Adicionar categoria";
        final ArrayList<String> displayList = new ArrayList<>(Arrays.asList(expenseCategories));
        displayList.add(ADD_NEW);

        ArrayAdapter<String> adapter = new ArrayAdapter<String>(this,
                android.R.layout.simple_list_item_1, displayList) {
            @Override
            public View getView(int position, View convertView, ViewGroup parent) {
                View view = super.getView(position, convertView, parent);
                TextView tv = (TextView) view.findViewById(android.R.id.text1);
                String item = displayList.get(position);
                if (item.equals(ADD_NEW)) {
                    view.setBackgroundColor(0xFFE8F5E9);
                    tv.setTextColor(0xFF1B5E20);
                    tv.setTextSize(14);
                } else if (selectedItems.contains(item)) {
                    view.setBackgroundColor(0xFFDDDDDD);
                    tv.setTextColor(Color.BLACK);
                } else {
                    view.setBackgroundColor(Color.WHITE);
                    tv.setTextColor(Color.BLACK);
                }
                return view;
            }
        };

        AlertDialog dialog = new AlertDialog.Builder(this)
            .setTitle("Selecionar categoria")
            .setAdapter(adapter, null)
            .setPositiveButton("Aplicar", (d, w) -> {
                if (!selectedItems.isEmpty()) {
                    StringBuilder catBuilder = new StringBuilder();
                    for (String cat : selectedItems) {
                        if (catBuilder.length() > 0) catBuilder.append("/");
                        catBuilder.append(cat);
                    }
                    addExpenseWithCategory(catBuilder.toString());
                }
            })
            .setNegativeButton("Cancelar", null)
            .setOnDismissListener(d -> {
                isMultiSelect[0] = false;
                selectedItems.clear();
            })
            .create();

        dialog.show();
        ListView listView = dialog.getListView();
        listView.setDescendantFocusability(ListView.FOCUS_BLOCK_DESCENDANTS);

        listView.setOnItemClickListener((parent, view, position, id) -> {
            String item = displayList.get(position);
            if (item.equals(ADD_NEW)) {
                dialog.dismiss();
                showAddCategoryDialog();
                return;
            }
            if (isMultiSelect[0]) {
                if (selectedItems.contains(item)) {
                    selectedItems.remove(item);
                } else {
                    selectedItems.add(item);
                }
                adapter.notifyDataSetChanged();
            } else {
                addExpenseWithCategory(item);
                dialog.dismiss();
            }
        });

        listView.setOnItemLongClickListener((parent, view, position, id) -> {
            String item = displayList.get(position);
            if (item.equals(ADD_NEW)) return false;
            isMultiSelect[0] = true;
            selectedItems.add(item);
            adapter.notifyDataSetChanged();
            Toast.makeText(this, "Modo múltiplo ativado. Toque em outros itens para selecionar.", Toast.LENGTH_SHORT).show();
            return true;
        });
    }

    private void showAddCategoryDialog() {
        EditText input = new EditText(this);
        input.setHint("Nome da categoria");
        input.setPadding(40, 20, 40, 20);
        input.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_FLAG_CAP_WORDS);
        new AlertDialog.Builder(this)
            .setTitle("Nova categoria")
            .setView(input)
            .setPositiveButton("Adicionar", (d, w) -> {
                String name = input.getText().toString().trim();
                if (!name.isEmpty()) {
                    boolean exists = false;
                    for (String cat : expenseCategories) {
                        if (cat.equalsIgnoreCase(name)) { exists = true; break; }
                    }
                    if (!exists) {
                        customCategories.add(name);
                        saveCustomCategories();
                        expenseCategories = getAllCategories();
                        Toast.makeText(this, "Categoria \"" + name + "\" adicionada!", Toast.LENGTH_SHORT).show();
                    } else {
                        Toast.makeText(this, "Categoria já existe.", Toast.LENGTH_SHORT).show();
                    }
                }
            })
            .setNegativeButton("Cancelar", null)
            .show();
    }

    private void refreshExpenseTotal() {
        double total = 0;
        double paid = 0;
        for (ExpenseItem e : expenseItems) {
            total += e.amount;
            if (e.paid) paid += e.amount;
        }
        expenseTotalDisplay.setText(currencyFormat.format(total));
        expensePaidDisplay.setText(currencyFormat.format(paid));
        double due = total - paid;
        expenseRemainingDisplay.setText(currencyFormat.format(due));
        expenseRemainingDisplay.setTextColor(due > 0 ? getResources().getColor(R.color.budgetWarning) : getResources().getColor(R.color.budgetDefault));
        boolean empty = expenseItems.isEmpty();
        expenseListView.setVisibility(empty ? View.GONE : View.VISIBLE);
        emptyExpensesText.setVisibility(empty ? View.VISIBLE : View.GONE);
        if (empty) {
            editingExpensePosition = -1;
        }
        if (financeBudgetLimit > 0) {
            financeBudgetLimitDisplay.setText(currencyFormat.format(financeBudgetLimit));
            double budgetRemain = financeBudgetLimit - paid;
            if (budgetRemain >= 0) {
                financeBudgetRemaining.setText("Restante: " + currencyFormat.format(budgetRemain));
                financeBudgetRemaining.setTextColor(getResources().getColor(R.color.budgetDefault));
            } else {
                financeBudgetRemaining.setText("Excedido: " + currencyFormat.format(-budgetRemain));
                financeBudgetRemaining.setTextColor(getResources().getColor(R.color.budgetWarning));
            }
        } else {
            financeBudgetLimitDisplay.setText(R.string.budget_click_hint);
            financeBudgetRemaining.setText("");
        }
        startBudgetBlink();
    }

    private void showSaveExpenseDialog() {
        if (expenseItems.isEmpty()) {
            Toast.makeText(this, "Nenhuma despesa para salvar.", Toast.LENGTH_SHORT).show();
            return;
        }
        String defaultTitle = "Despesas Financeiras - " + new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault()).format(new Date());
        EditText titleInput = new EditText(this);
        titleInput.setText(defaultTitle);
        titleInput.selectAll();
        titleInput.setPadding(40, 20, 40, 20);
        titleInput.setHint("Título");

        LinearLayout container = new LinearLayout(this);
        container.setOrientation(LinearLayout.VERTICAL);
        container.setPadding(40, 20, 40, 20);
        TextView label = new TextView(this);
        label.setText("Dê um título para este relatório:");
        label.setTextSize(14);
        container.addView(label);
        container.addView(titleInput);

        AlertDialog.Builder builder = new AlertDialog.Builder(this)
            .setTitle("Salvar despesas")
            .setView(container);

        if (currentExpenseFile != null) {
            String fileName = currentExpenseFile.getName();
            builder.setPositiveButton("Atualizar \"" + fileName + "\"", (d, w) -> {
                saveExpensesToFile(currentExpenseFile);
                Toast.makeText(this, "Arquivo atualizado: " + fileName, Toast.LENGTH_SHORT).show();
            });
            builder.setNegativeButton("Salvar como novo", (d, w) -> {
                String title = titleInput.getText().toString().trim();
                if (title.isEmpty()) title = defaultTitle;
                saveExpensesToTimestampedFile(title);
                Toast.makeText(this, "Novo arquivo salvo com sucesso!", Toast.LENGTH_SHORT).show();
                switchTab(1);
            });
        } else {
            builder.setPositiveButton("Salvar e continuar", (d, w) -> {
                String title = titleInput.getText().toString().trim();
                if (title.isEmpty()) title = defaultTitle;
                saveExpensesToTimestampedFile(title);
                Toast.makeText(this, "Despesas salvas com sucesso!", Toast.LENGTH_SHORT).show();
            });
            builder.setNegativeButton("Apenas Salvar", (d, w) -> {
                String title = titleInput.getText().toString().trim();
                if (title.isEmpty()) title = defaultTitle;
                saveExpensesToTimestampedFile(title);
                Toast.makeText(this, "Despesas salvas com sucesso!", Toast.LENGTH_SHORT).show();
                switchTab(1);
            });
        }
        builder.show();
    }

    private void enterExpensePaidMode() {
        expensePaidMode = true;
        btnConcluirPaid.setVisibility(View.VISIBLE);
        btnConcluirPaid.setBackgroundResource(R.drawable.bg_concluir_neon);
        btnConcluirPaid.setTextColor(Color.WHITE);
        AlphaAnimation blink = new AlphaAnimation(1f, 0.3f);
        blink.setDuration(500);
        blink.setRepeatMode(Animation.REVERSE);
        blink.setRepeatCount(Animation.INFINITE);
        btnConcluirPaid.startAnimation(blink);
        expenseAdapter.notifyDataSetChanged();
        Toast.makeText(this, "Toque no visto para marcar como pago", Toast.LENGTH_SHORT).show();
    }

    private void exitExpensePaidMode() {
        expensePaidMode = false;
        btnConcluirPaid.clearAnimation();
        btnConcluirPaid.setVisibility(View.GONE);
        btnConcluirPaid.setBackgroundResource(android.R.drawable.btn_default);
        btnConcluirPaid.setTextColor(Color.WHITE);
        expenseAdapter.notifyDataSetChanged();
    }

    private void clearAllExpenses() {
        if (expenseItems.isEmpty()) {
            Toast.makeText(this, R.string.exp_empty, Toast.LENGTH_SHORT).show();
            return;
        }
        exitExpensePaidMode();
        expenseItems.clear();
        editingExpensePosition = -1;
        expenseAdapter.notifyDataSetChanged();
        refreshExpenseTotal();
        Toast.makeText(this, "Tela limpa. Dados salvos permanecem intactos.", Toast.LENGTH_SHORT).show();
    }

    private void showExpenseReport() {
        java.util.Map<String, Double> byCategory = new java.util.LinkedHashMap<>();
        for (String cat : expenseCategories) {
            byCategory.put(cat, 0.0);
        }
        double grandTotal = 0;
        for (ExpenseItem e : expenseItems) {
            Double cur = byCategory.get(e.category);
            if (cur == null) cur = 0.0;
            byCategory.put(e.category, cur + e.amount);
            grandTotal += e.amount;
        }

        StringBuilder report = new StringBuilder();
        for (java.util.Map.Entry<String, Double> entry : byCategory.entrySet()) {
            if (entry.getValue() > 0) {
                double pct = (entry.getValue() / grandTotal) * 100;
                report.append(entry.getKey()).append(": ")
                    .append(currencyFormat.format(entry.getValue()))
                    .append(" (").append(String.format(Locale.US, "%.0f", pct)).append("%)\n");
            }
        }
        if (report.length() == 0) {
            report.append("Nenhuma despesa registrada.");
        } else {
            report.append("\nTotal: ").append(currencyFormat.format(grandTotal));
        }

        new AlertDialog.Builder(this)
            .setTitle(R.string.exp_report_title)
            .setMessage(report.toString().trim())
            .setPositiveButton(R.string.ok, null)
            .show();
    }

    private void switchListasSubTab(int index) {
        expMarketContent.setVisibility(index == 0 ? View.VISIBLE : View.GONE);
        expFinanceFilesContent.setVisibility(index == 1 ? View.VISIBLE : View.GONE);

        int activeColor = getResources().getColor(R.color.headerText);
        int inactiveColor = getResources().getColor(R.color.textSecondary);
        expTabMarket.setTextColor(index == 0 ? activeColor : inactiveColor);
        expTabMarket.setBackgroundResource(index == 0 ? R.drawable.bg_tab_active : 0);
        expTabFinance.setTextColor(index == 1 ? activeColor : inactiveColor);
        expTabFinance.setBackgroundResource(index == 1 ? R.drawable.bg_tab_active : 0);

        if (index == 0) {
            refreshExpensesMarket();
            exitMarketSelectionMode();
        } else {
            exitMarketSelectionMode();
            refreshFinanceFiles();
        }
    }

    private void refreshExpensesMarket() {
        exitMarketSelectionMode();
        marketListFiles.clear();
        File dir = getListasDir();
        if (dir != null && dir.exists()) {
            File[] files = dir.listFiles((d, name) ->
                (name.startsWith("lista_compras_") || name.startsWith("modelo_")) && name.endsWith(".json"));
            if (files != null) {
                marketListFiles.addAll(Arrays.asList(files));
                Collections.sort(marketListFiles, (a, b) -> Long.compare(b.lastModified(), a.lastModified()));
            }
        }
        ((BaseAdapter) expMarketListView.getAdapter()).notifyDataSetChanged();
        boolean empty = marketListFiles.isEmpty();
        expMarketListView.setVisibility(empty ? View.GONE : View.VISIBLE);
        expMarketEmptyText.setVisibility(empty ? View.VISIBLE : View.GONE);
    }

    private File getListasDir() {
        File base = getExternalFilesDir(null);
        if (base == null) base = getFilesDir();
        File dir = new File(base, "listas_pessoais");
        if (!dir.exists()) dir.mkdirs();
        return dir;
    }

    private void saveExpensesToFile(File file) {
        try {
            JSONObject root = new JSONObject();
            root.put("version", 1);
            JSONArray arr = new JSONArray();
            for (ExpenseItem e : expenseItems) {
                JSONObject obj = new JSONObject();
                obj.put("description", e.description);
                obj.put("amount", e.amount);
                obj.put("category", e.category);
                obj.put("date", e.date);
                obj.put("paid", e.paid);
                arr.put(obj);
            }
            root.put("expenses", arr);
            File tmp = new File(file.getParentFile(), file.getName() + ".tmp");
            FileWriter fw = new FileWriter(tmp);
            fw.write(root.toString(2));
            fw.close();
            if (file.exists()) file.delete();
            tmp.renameTo(file);
        } catch (Exception e) {
            Log.e("SuperCalc", "Error saving expenses to " + file.getName(), e);
        }
    }

    private void saveExpensesToFile() {
        File dir = getListasDir();
        try {
            JSONObject root = new JSONObject();
            root.put("version", 1);
            JSONArray arr = new JSONArray();
            for (ExpenseItem e : expenseItems) {
                JSONObject obj = new JSONObject();
                obj.put("description", e.description);
                obj.put("amount", e.amount);
                obj.put("category", e.category);
                obj.put("date", e.date);
                obj.put("paid", e.paid);
                arr.put(obj);
            }
            root.put("expenses", arr);
            File tmp = new File(dir, "despesas.json.tmp");
            File target = new File(dir, "despesas.json");
            FileWriter fw = new FileWriter(tmp);
            fw.write(root.toString(2));
            fw.close();
            // Atomic replace: tmp → target
            if (target.exists()) target.delete();
            tmp.renameTo(target);
        } catch (Exception e) {
            Log.e("SuperCalc", "Error saving expenses", e);
        }
    }

    private void saveExpensesToTimestampedFile(String title) {
        File dir = getListasDir();
        String timestamp = new SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", Locale.getDefault()).format(new Date());
        try {
            JSONObject root = new JSONObject();
            root.put("version", 1);
            root.put("title", title);
            root.put("date", timestamp);
            root.put("prefix", "despesas");
            JSONArray arr = new JSONArray();
            for (ExpenseItem e : expenseItems) {
                JSONObject obj = new JSONObject();
                obj.put("description", e.description);
                obj.put("amount", e.amount);
                obj.put("category", e.category);
                obj.put("date", e.date);
                obj.put("paid", e.paid);
                arr.put(obj);
            }
            root.put("expenses", arr);
            File file = new File(dir, "despesas_" + timestamp + ".json");
            FileWriter fw = new FileWriter(file);
            fw.write(root.toString(2));
            fw.close();
            refreshFinanceFiles();
        } catch (Exception e) {
            Log.e("SuperCalc", "Error saving timestamped expenses", e);
        }
    }

    private void loadCustomCategories() {
        SharedPreferences prefs = getSharedPreferences("supermarket_prefs", MODE_PRIVATE);
        String json = prefs.getString("custom_categories", "[]");
        try {
            JSONArray arr = new JSONArray(json);
            customCategories.clear();
            for (int i = 0; i < arr.length(); i++) {
                customCategories.add(arr.getString(i));
            }
        } catch (Exception e) {
            customCategories.clear();
        }
    }

    private void saveCustomCategories() {
        SharedPreferences prefs = getSharedPreferences("supermarket_prefs", MODE_PRIVATE);
        JSONArray arr = new JSONArray();
        for (String cat : customCategories) {
            arr.put(cat);
        }
        prefs.edit().putString("custom_categories", arr.toString()).apply();
    }

    private String[] getAllCategories() {
        String[] base = {
            getString(R.string.exp_cat_water),
            getString(R.string.exp_cat_energy),
            getString(R.string.exp_cat_gas),
            getString(R.string.exp_cat_phone),
            getString(R.string.exp_cat_internet),
            getString(R.string.exp_cat_rent),
            getString(R.string.exp_cat_condo),
            getString(R.string.exp_cat_pharmacy),
            getString(R.string.exp_cat_transport),
            getString(R.string.exp_cat_education),
            getString(R.string.exp_cat_leisure),
            getString(R.string.exp_cat_insurance),
            getString(R.string.exp_cat_subs),
            getString(R.string.exp_cat_other)
        };
        ArrayList<String> all = new ArrayList<>(Arrays.asList(base));
        all.addAll(customCategories);
        return all.toArray(new String[0]);
    }

    private void loadExpensesFromFile() {
        loadExpensesFromFile(new File(getListasDir(), "despesas.json"));
    }

    private void loadExpensesFromFile(File file) {
        if (!file.exists()) return;
        exitExpensePaidMode();
        currentExpenseFile = file;
        try {
            BufferedReader br = new BufferedReader(new FileReader(file));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
            br.close();
            JSONObject root = new JSONObject(sb.toString());
            JSONArray arr = root.getJSONArray("expenses");
            expenseItems.clear();
            for (int i = 0; i < arr.length(); i++) {
                JSONObject obj = arr.getJSONObject(i);
                ExpenseItem e = new ExpenseItem(
                    obj.getString("description"),
                    obj.getDouble("amount"),
                    obj.getString("category")
                );
                e.date = obj.optLong("date", System.currentTimeMillis());
                e.paid = obj.optBoolean("paid", false);
                expenseItems.add(e);
            }
            editingExpensePosition = -1;
            expenseAdapter.notifyDataSetChanged();
            refreshExpenseTotal();
        } catch (Exception e) {
            Log.e("SuperCalc", "Error loading expenses", e);
        }
    }

    // ==================== SETTINGS ====================

    private void setupSettings() {
        RadioGroup themeGroup = findViewById(R.id.themeGroup);
        RadioGroup skinGroup = findViewById(R.id.skinGroup);
        CheckBox chkShowOps = findViewById(R.id.chkShowOps);
        CheckBox chkShowBack = findViewById(R.id.chkShowBack);
        CheckBox chkShowClear = findViewById(R.id.chkShowClear);
        CheckBox chkShow00 = findViewById(R.id.chkShow00);

        int themeId = currentTheme == THEME_DARK ? R.id.themeDark
            : currentTheme == THEME_BLUE ? R.id.themeBlue : R.id.themeDefault;
        themeGroup.check(themeId);

        int skinId = currentSkin == SKIN_ROUNDED ? R.id.skinRounded : R.id.skinDefault;
        skinGroup.check(skinId);

        chkShowOps.setChecked(showOps);
        chkShowBack.setChecked(showBack);
        chkShowClear.setChecked(showClear);
        chkShow00.setChecked(show00);

        themeGroup.setOnCheckedChangeListener((g, id) -> {
            if (id == R.id.themeDefault) currentTheme = THEME_DEFAULT;
            else if (id == R.id.themeDark) currentTheme = THEME_DARK;
            else if (id == R.id.themeBlue) currentTheme = THEME_BLUE;
            saveSettings();
            applyTheme();
        });

        skinGroup.setOnCheckedChangeListener((g, id) -> {
            currentSkin = (id == R.id.skinRounded) ? SKIN_ROUNDED : SKIN_DEFAULT;
            saveSettings();
            applySkin();
        });

        chkShowOps.setOnCheckedChangeListener((b, checked) -> {
            showOps = checked;
            saveSettings();
            applyNumpadCustomization();
        });

        chkShowBack.setOnCheckedChangeListener((b, checked) -> {
            showBack = checked;
            saveSettings();
            applyNumpadCustomization();
        });

        chkShowClear.setOnCheckedChangeListener((b, checked) -> {
            showClear = checked;
            saveSettings();
            applyNumpadCustomization();
        });

        chkShow00.setOnCheckedChangeListener((b, checked) -> {
            show00 = checked;
            saveSettings();
            applyNumpadCustomization();
        });
    }

    // ==================== THEME / SKIN ====================

    private int getColorForCurrentTheme(boolean isText) {
        if (currentTheme == THEME_DARK) {
            return isText ? getResources().getColor(R.color.darkTextPrimary) : getResources().getColor(R.color.budgetPositive);
        }
        return isText ? getResources().getColor(R.color.textPrimary) : getResources().getColor(R.color.budgetPositive);
    }

    private void applyTheme() {
        switch (currentTheme) {
            case THEME_DARK:
                rootLayout.setBackgroundColor(getResources().getColor(R.color.darkBg));
                headerBar.setBackgroundColor(Color.parseColor("#1a1a1a"));
                tabBar.setBackgroundColor(Color.parseColor("#0d0d0d"));
                numpadContainer.setBackgroundColor(getResources().getColor(R.color.darkCard));
                priceDisplay.setBackgroundResource(R.drawable.bg_input_dark);
                priceDisplay.setTextColor(getResources().getColor(R.color.darkTextPrimary));
                totalDisplay.setTextColor(getResources().getColor(R.color.darkTextPrimary));
                budgetLimitDisplay.setTextColor(getResources().getColor(R.color.darkTextPrimary));
                break;

            case THEME_BLUE:
                rootLayout.setBackgroundColor(getResources().getColor(R.color.background));
                headerBar.setBackgroundColor(getResources().getColor(R.color.blueDark));
                tabBar.setBackgroundColor(getResources().getColor(R.color.blueDark));
                numpadContainer.setBackgroundColor(getResources().getColor(R.color.cardBg));
                priceDisplay.setTextColor(getResources().getColor(R.color.textPrimary));
                totalDisplay.setTextColor(getResources().getColor(R.color.bluePrimary));
                budgetLimitDisplay.setTextColor(getResources().getColor(R.color.bluePrimary));
                break;

            default:
                rootLayout.setBackgroundColor(getResources().getColor(R.color.background));
                headerBar.setBackgroundColor(getResources().getColor(R.color.headerBg));
                tabBar.setBackgroundColor(getResources().getColor(R.color.primaryDark));
                numpadContainer.setBackgroundColor(getResources().getColor(R.color.cardBg));
                priceDisplay.setTextColor(getResources().getColor(R.color.textPrimary));
                totalDisplay.setTextColor(getResources().getColor(R.color.totalColor));
                budgetLimitDisplay.setTextColor(getResources().getColor(R.color.primary));
                break;
        }
    }

    private void applySkin() {
        int numpadBgRes = (currentSkin == SKIN_ROUNDED)
            ? R.drawable.bg_numpad_rounded : R.drawable.btn_numpad;
        int actionBgRes = (currentSkin == SKIN_ROUNDED)
            ? R.drawable.bg_action_rounded : R.drawable.btn_action;

        int[] numpadOnly = {
            R.id.btnN0, R.id.btnN1, R.id.btnN2, R.id.btnN3, R.id.btnN4,
            R.id.btnN5, R.id.btnN6, R.id.btnN7, R.id.btnN8, R.id.btnN9,
            R.id.btnN00, R.id.btnNComma, R.id.btnOpAdd, R.id.btnOpSub,
            R.id.btnOpMul, R.id.btnOpDiv
        };
        int[] actionOnly = {
            R.id.btnNBack, R.id.btnNClear, R.id.btnOpEq, R.id.addButton, R.id.clearButton
        };

        for (int id : numpadOnly) {
            View v = calculatorPage.findViewById(id);
            if (v != null) v.setBackgroundResource(numpadBgRes);
        }
        for (int id : actionOnly) {
            View v = calculatorPage.findViewById(id);
            if (v != null) v.setBackgroundResource(actionBgRes);
        }
    }

    private void applyNumpadCustomization() {
        opsRow.setVisibility(showOps ? View.VISIBLE : View.GONE);
        setButtonHidden(btnNBack, !showBack);
        setButtonHidden(btnNClear, !showClear);
        setButtonHidden(btnN00, !show00);
    }

    private void setButtonHidden(Button btn, boolean hidden) {
        btn.setVisibility(View.VISIBLE);
        btn.setAlpha(hidden ? 0f : 1f);
        btn.setEnabled(!hidden);
        btn.setClickable(!hidden);
    }

    // ==================== LISTENER CALLBACKS ====================

    @Override
    public void onIncrement(int position) {
        if (position >= 0 && position < items.size()) {
            items.get(position).increment();
            adapter.notifyDataSetChanged();
            updateTotal();
        }
    }

    @Override
    public void onDecrement(int position) {
        if (position >= 0 && position < items.size()) {
            items.get(position).decrement();
            adapter.notifyDataSetChanged();
            updateTotal();
        }
    }

    @Override
    public void onRemove(int position) {
        if (position >= 0 && position < items.size()) {
            items.remove(position);
            adapter.notifyDataSetChanged();
            updateTotal();
            if (editingIndex == position) {
                editingIndex = -1;
                adapter.setEditingPosition(-1);
            } else if (editingIndex > position) {
                editingIndex--;
                adapter.setEditingPosition(editingIndex);
            }
        }
    }

    @Override
    public void onItemClick(int position) {
        if (position >= 0 && position < items.size()) {
            loadItemForEditing(position);
        }
    }

    @Override
    public void onNameChanged(int position, String name) {
        if (position >= 0 && position < items.size()) {
            items.get(position).setName(name);
        }
    }
}
