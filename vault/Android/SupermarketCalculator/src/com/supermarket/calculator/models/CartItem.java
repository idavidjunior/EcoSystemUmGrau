package com.supermarket.calculator.models;

public class CartItem {
    private String name;
    private double unitPrice;
    private int quantity;

    public CartItem(String name, double unitPrice, int quantity) {
        this.name = name;
        this.unitPrice = unitPrice;
        this.quantity = quantity;
    }

    public String getName() { return name; }
    public double getUnitPrice() { return unitPrice; }
    public int getQuantity() { return quantity; }
    public double getTotal() { return unitPrice * quantity; }

    public void setName(String name) { this.name = name; }
    public void setUnitPrice(double unitPrice) { this.unitPrice = unitPrice; }

    public void setQuantity(int quantity) {
        this.quantity = Math.max(0, quantity);
    }

    public void increment() { this.quantity++; }
    public void decrement() { if (this.quantity > 1) this.quantity--; }
}
