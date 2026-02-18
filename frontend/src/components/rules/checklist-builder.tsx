"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  CheckSquare,
  Plus,
  X,
  ChevronUp,
  ChevronDown,
  GripVertical,
} from "lucide-react";
import { useSettingsStore } from "@/stores/settings-store";
import type { ChecklistItem } from "@/types";

export function ChecklistBuilder() {
  const { rules, updateRules } = useSettingsStore();
  const [newItem, setNewItem] = useState("");

  const addItem = () => {
    if (!newItem.trim()) return;
    
    const updatedChecklist = [
      ...rules.checklist,
      {
        id: `c${Date.now()}`,
        label: newItem.trim(),
        required: false,
        order: rules.checklist.length + 1,
      },
    ];
    
    updateRules({ checklist: updatedChecklist });
    setNewItem("");
  };

  const removeItem = (id: string) => {
    const updatedChecklist = rules.checklist
      .filter((item) => item.id !== id)
      .map((item, index) => ({ ...item, order: index + 1 }));
    
    updateRules({ checklist: updatedChecklist });
  };

  const updateItem = (id: string, updates: Partial<ChecklistItem>) => {
    const updatedChecklist = rules.checklist.map((item) =>
      item.id === id ? { ...item, ...updates } : item
    );
    
    updateRules({ checklist: updatedChecklist });
  };

  const moveItem = (id: string, direction: "up" | "down") => {
    const currentIndex = rules.checklist.findIndex((item) => item.id === id);
    if (currentIndex === -1) return;
    
    const newIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0 || newIndex >= rules.checklist.length) return;
    
    const updatedChecklist = [...rules.checklist];
    [updatedChecklist[currentIndex], updatedChecklist[newIndex]] = [
      updatedChecklist[newIndex],
      updatedChecklist[currentIndex],
    ];
    
    // Update order numbers
    const reorderedChecklist = updatedChecklist.map((item, index) => ({
      ...item,
      order: index + 1,
    }));
    
    updateRules({ checklist: reorderedChecklist });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <CheckSquare className="h-4 w-4 text-emerald-400" />
          Pre-Trade Checklist
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Existing Items */}
        <div className="space-y-2">
          {rules.checklist
            .sort((a, b) => a.order - b.order)
            .map((item, index) => (
              <div
                key={item.id}
                className="flex items-center gap-2 p-3 rounded-lg bg-slate-800/50 border border-slate-700 group"
              >
                {/* Drag handle */}
                <div className="flex flex-col gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-4 w-4 p-0 text-slate-400 hover:text-slate-200"
                    onClick={() => moveItem(item.id, "up")}
                    disabled={index === 0}
                  >
                    <ChevronUp className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-4 w-4 p-0 text-slate-400 hover:text-slate-200"
                    onClick={() => moveItem(item.id, "down")}
                    disabled={index === rules.checklist.length - 1}
                  >
                    <ChevronDown className="h-3 w-3" />
                  </Button>
                </div>

                {/* Item content */}
                <div className="flex-1 min-w-0">
                  <Input
                    value={item.label}
                    onChange={(e) =>
                      updateItem(item.id, { label: e.target.value })
                    }
                    className="bg-transparent border-none p-0 text-sm text-slate-200 focus:ring-0"
                    placeholder="Checklist item..."
                  />
                </div>

                {/* Required toggle */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Required</span>
                  <Switch
                    checked={item.required}
                    onCheckedChange={(checked) =>
                      updateItem(item.id, { required: checked })
                    }
                  />
                </div>

                {/* Delete button */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-slate-400 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => removeItem(item.id)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
        </div>

        {/* Add new item */}
        <div className="flex gap-2">
          <Input
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            placeholder="Add new checklist item..."
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addItem();
              }
            }}
          />
          <Button onClick={addItem} size="icon" disabled={!newItem.trim()}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        {/* Instructions */}
        <div className="text-xs text-slate-400 bg-slate-800/30 p-3 rounded-lg">
          <p className="mb-1">
            ✓ <strong>Required items</strong> must be checked before opening trades
          </p>
          <p>
            ✓ Use up/down arrows to reorder items by priority
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
