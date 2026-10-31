import React, { useState, useMemo } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useChatStore } from "../../store/useChatStore";
import { useUIStore } from "../../store/useUIStore";
import { useSettingsStore } from "../../store/useSettingsStore";
import {
  MessageSquare,
  Plus,
  Search,
  BookOpen,
  Network,
  BarChart3,
  Settings as SettingsIcon,
  Pin,
  Trash2,
  Edit2,
  Moon,
  Sun,
  Activity,
  X,
  PanelLeftClose,
} from "lucide-react";
import { cn } from "../../lib/utils";

export function Sidebar() {
  const navigate = useNavigate();
  const {
    conversations,
    activeConversationId,
    createConversation,
    selectConversation,
    deleteConversation,
    renameConversation,
    togglePinConversation,
    searchFilter,
    setSearchFilter,
  } = useChatStore();

  const { isSidebarOpen, setSidebarOpen } = useUIStore();
  const { theme, setTheme } = useSettingsStore();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  // Group conversations by time buckets: Today, Yesterday, Previous 7 Days, Older
  const groupedConversations = useMemo(() => {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterdayStart = todayStart - 86400000;
    const sevenDaysAgo = todayStart - 7 * 86400000;

    const filtered = conversations.filter((c) =>
      c.title.toLowerCase().includes(searchFilter.toLowerCase())
    );

    const pinned = filtered.filter((c) => c.isPinned);
    const unpinned = filtered.filter((c) => !c.isPinned);

    const today: typeof filtered = [];
    const yesterday: typeof filtered = [];
    const last7Days: typeof filtered = [];
    const older: typeof filtered = [];

    unpinned.forEach((c) => {
      if (c.updatedAt >= todayStart) {
        today.push(c);
      } else if (c.updatedAt >= yesterdayStart) {
        yesterday.push(c);
      } else if (c.updatedAt >= sevenDaysAgo) {
        last7Days.push(c);
      } else {
        older.push(c);
      }
    });

    return { pinned, today, yesterday, last7Days, older };
  }, [conversations, searchFilter]);

  const handleStartRename = (id: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(id);
    setEditingTitle(currentTitle);
  };

  const handleSaveRename = (id: string) => {
    if (editingTitle.trim()) {
      renameConversation(id, editingTitle.trim());
    }
    setEditingId(null);
  };

  const handleNewChat = () => {
    const id = createConversation();
    navigate("/chat");
    selectConversation(id);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isSidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/40 z-30 md:hidden backdrop-blur-sm"
        />
      )}

      <aside
        className={cn(
          "fixed md:static inset-y-0 left-0 z-40 w-60 flex flex-col bg-parchment-container-low dark:bg-darkpaper-surface border-r border-parchment-outline-variant transition-transform duration-200 select-none",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0 md:w-0 md:overflow-hidden md:border-r-0"
        )}
      >
        {/* App Title Header */}
        <div className="p-3 border-b border-parchment-outline-variant flex items-center justify-between bg-parchment-container-low/70">
          <div>
            <div className="font-serif font-medium text-sm text-parchment-primary dark:text-darkpaper-primary tracking-tight leading-tight">
              Research Assistant
            </div>
            <div className="text-[9px] font-mono tracking-label-wide uppercase text-parchment-secondary mt-0.5">
              Hybrid RAG Platform
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden p-1 text-parchment-secondary hover:text-parchment-primary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Button & Search */}
        <div className="p-2.5 space-y-2 border-b border-parchment-outline-variant/60">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 px-2.5 bg-parchment-primary text-parchment-on-primary hover:bg-parchment-primary-container font-serif text-xs font-medium tracking-wide border border-parchment-primary dark:bg-darkpaper-primary dark:text-darkpaper-on-primary transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Research Inquiry</span>
          </button>

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-parchment-secondary" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search dialogues..."
              className="w-full pl-8 pr-2.5 py-1 text-xs font-serif bg-parchment-container-lowest dark:bg-darkpaper-container border border-parchment-outline-variant text-parchment-on-surface placeholder:text-parchment-secondary/70 outline-none focus:border-parchment-primary"
            />
          </div>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto px-2 py-2 space-y-4">
          {/* Empty History Placeholder */}
          {groupedConversations.pinned.length === 0 &&
            groupedConversations.today.length === 0 &&
            groupedConversations.yesterday.length === 0 &&
            groupedConversations.last7Days.length === 0 &&
            groupedConversations.older.length === 0 && (
              <div className="py-12 px-4 text-center select-none">
                <div className="w-8 h-8 mx-auto mb-2 flex items-center justify-center border border-dashed border-parchment-outline-variant text-parchment-secondary">
                  <BookOpen className="w-3.5 h-3.5 opacity-50" />
                </div>
                <p className="text-xs font-serif text-parchment-on-surface-variant font-medium">
                  No saved dialogues
                </p>
                <p className="text-[10px] font-mono text-parchment-outline mt-0.5">
                  Research queries & citations will be indexed here
                </p>
              </div>
            )}

          {/* Pinned Section */}
          {groupedConversations.pinned.length > 0 && (
            <div>
              <div className="px-2 mb-1 text-[10px] font-mono tracking-label uppercase text-parchment-secondary flex items-center gap-1">
                <Pin className="w-2.5 h-2.5" />
                <span>Pinned Inquiries</span>
              </div>
              {groupedConversations.pinned.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conv={conv}
                  isActive={activeConversationId === conv.id}
                  isEditing={editingId === conv.id}
                  editingTitle={editingTitle}
                  setEditingTitle={setEditingTitle}
                  onSelect={() => {
                    selectConversation(conv.id);
                    navigate("/chat");
                  }}
                  onPin={(e) => {
                    e.stopPropagation();
                    togglePinConversation(conv.id);
                  }}
                  onDelete={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  onStartRename={(e) => handleStartRename(conv.id, conv.title, e)}
                  onSaveRename={() => handleSaveRename(conv.id)}
                />
              ))}
            </div>
          )}

          {/* Today */}
          {groupedConversations.today.length > 0 && (
            <div>
              <div className="px-2 mb-1 text-[10px] font-mono tracking-label uppercase text-parchment-secondary">
                Today
              </div>
              {groupedConversations.today.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conv={conv}
                  isActive={activeConversationId === conv.id}
                  isEditing={editingId === conv.id}
                  editingTitle={editingTitle}
                  setEditingTitle={setEditingTitle}
                  onSelect={() => {
                    selectConversation(conv.id);
                    navigate("/chat");
                  }}
                  onPin={(e) => {
                    e.stopPropagation();
                    togglePinConversation(conv.id);
                  }}
                  onDelete={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  onStartRename={(e) => handleStartRename(conv.id, conv.title, e)}
                  onSaveRename={() => handleSaveRename(conv.id)}
                />
              ))}
            </div>
          )}

          {/* Yesterday */}
          {groupedConversations.yesterday.length > 0 && (
            <div>
              <div className="px-2 mb-1 text-[10px] font-mono tracking-label uppercase text-parchment-secondary">
                Yesterday
              </div>
              {groupedConversations.yesterday.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conv={conv}
                  isActive={activeConversationId === conv.id}
                  isEditing={editingId === conv.id}
                  editingTitle={editingTitle}
                  setEditingTitle={setEditingTitle}
                  onSelect={() => {
                    selectConversation(conv.id);
                    navigate("/chat");
                  }}
                  onPin={(e) => {
                    e.stopPropagation();
                    togglePinConversation(conv.id);
                  }}
                  onDelete={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  onStartRename={(e) => handleStartRename(conv.id, conv.title, e)}
                  onSaveRename={() => handleSaveRename(conv.id)}
                />
              ))}
            </div>
          )}

          {/* Previous 7 Days */}
          {groupedConversations.last7Days.length > 0 && (
            <div>
              <div className="px-2 mb-1 text-[10px] font-mono tracking-label uppercase text-parchment-secondary">
                Previous 7 Days
              </div>
              {groupedConversations.last7Days.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conv={conv}
                  isActive={activeConversationId === conv.id}
                  isEditing={editingId === conv.id}
                  editingTitle={editingTitle}
                  setEditingTitle={setEditingTitle}
                  onSelect={() => {
                    selectConversation(conv.id);
                    navigate("/chat");
                  }}
                  onPin={(e) => {
                    e.stopPropagation();
                    togglePinConversation(conv.id);
                  }}
                  onDelete={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  onStartRename={(e) => handleStartRename(conv.id, conv.title, e)}
                  onSaveRename={() => handleSaveRename(conv.id)}
                />
              ))}
            </div>
          )}

          {/* Older */}
          {groupedConversations.older.length > 0 && (
            <div>
              <div className="px-2 mb-1 text-[10px] font-mono tracking-label uppercase text-parchment-secondary">
                Older Inquiries
              </div>
              {groupedConversations.older.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conv={conv}
                  isActive={activeConversationId === conv.id}
                  isEditing={editingId === conv.id}
                  editingTitle={editingTitle}
                  setEditingTitle={setEditingTitle}
                  onSelect={() => {
                    selectConversation(conv.id);
                    navigate("/chat");
                  }}
                  onPin={(e) => {
                    e.stopPropagation();
                    togglePinConversation(conv.id);
                  }}
                  onDelete={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  onStartRename={(e) => handleStartRename(conv.id, conv.title, e)}
                  onSaveRename={() => handleSaveRename(conv.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Navigation Links */}
        <div className="p-2 border-t border-parchment-outline-variant space-y-0.5 text-xs font-serif bg-parchment-container/40 select-none">
          <NavLink
            to="/chat"
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 px-2.5 py-1.5 transition-colors border-l-2",
                isActive
                  ? "bg-parchment-container text-parchment-primary font-medium border-parchment-primary dark:bg-darkpaper-container dark:border-darkpaper-primary"
                  : "border-transparent text-parchment-on-surface-variant hover:bg-parchment-container/50 hover:text-parchment-primary"
              )
            }
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chat Assistant</span>
          </NavLink>

          <NavLink
            to="/papers"
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 px-2.5 py-1.5 transition-colors border-l-2",
                isActive
                  ? "bg-parchment-container text-parchment-primary font-medium border-parchment-primary dark:bg-darkpaper-container dark:border-darkpaper-primary"
                  : "border-transparent text-parchment-on-surface-variant hover:bg-parchment-container/50 hover:text-parchment-primary"
              )
            }
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Research Papers</span>
          </NavLink>

          <NavLink
            to="/graph"
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 px-2.5 py-1.5 transition-colors border-l-2",
                isActive
                  ? "bg-parchment-container text-parchment-primary font-medium border-parchment-primary dark:bg-darkpaper-container dark:border-darkpaper-primary"
                  : "border-transparent text-parchment-on-surface-variant hover:bg-parchment-container/50 hover:text-parchment-primary"
              )
            }
          >
            <Network className="w-3.5 h-3.5" />
            <span>Knowledge Graph</span>
          </NavLink>

          <NavLink
            to="/analytics"
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 px-2.5 py-1.5 transition-colors border-l-2",
                isActive
                  ? "bg-parchment-container text-parchment-primary font-medium border-parchment-primary dark:bg-darkpaper-container dark:border-darkpaper-primary"
                  : "border-transparent text-parchment-on-surface-variant hover:bg-parchment-container/50 hover:text-parchment-primary"
              )
            }
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Trends & Evaluation</span>
          </NavLink>

          <NavLink
            to="/settings"
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 px-2.5 py-1.5 transition-colors border-l-2",
                isActive
                  ? "bg-parchment-container text-parchment-primary font-medium border-parchment-primary dark:bg-darkpaper-container dark:border-darkpaper-primary"
                  : "border-transparent text-parchment-on-surface-variant hover:bg-parchment-container/50 hover:text-parchment-primary"
              )
            }
          >
            <SettingsIcon className="w-3.5 h-3.5" />
            <span>Settings</span>
          </NavLink>
        </div>

        {/* Footer: Theme Switcher */}
        <div className="p-2.5 border-t border-parchment-outline-variant bg-parchment-container-low dark:bg-darkpaper-surface flex items-center justify-end text-xs select-none">
          {/* Theme Toggle */}
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-1.5 border border-parchment-outline-variant hover:bg-parchment-container text-parchment-secondary hover:text-parchment-primary transition-colors cursor-pointer"
            title="Toggle Light / Dark mode"
          >
            {theme === "dark" ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
          </button>
        </div>
      </aside>
    </>
  );
}

function ConversationItem({
  conv,
  isActive,
  isEditing,
  editingTitle,
  setEditingTitle,
  onSelect,
  onPin,
  onDelete,
  onStartRename,
  onSaveRename,
}: {
  conv: any;
  isActive: boolean;
  isEditing: boolean;
  editingTitle: string;
  setEditingTitle: (v: string) => void;
  onSelect: () => void;
  onPin: (e: React.MouseEvent) => void;
  onDelete: (e: React.MouseEvent) => void;
  onStartRename: (e: React.MouseEvent) => void;
  onSaveRename: () => void;
}) {
  return (
    <div
      onClick={onSelect}
      className={cn(
        "group relative flex items-center justify-between px-2.5 py-1.5 my-0.5 text-xs font-serif cursor-pointer transition-colors border",
        isActive
          ? "bg-parchment-container text-parchment-primary border-parchment-outline dark:bg-darkpaper-container dark:text-darkpaper-primary font-medium"
          : "border-transparent text-parchment-on-surface-variant hover:bg-parchment-container/60 hover:text-parchment-on-surface"
      )}
    >
      <div className="flex items-center gap-2 truncate flex-1 min-w-0 pr-1">
        <MessageSquare className="w-3 h-3 flex-shrink-0 opacity-60" />
        {isEditing ? (
          <input
            type="text"
            value={editingTitle}
            onChange={(e) => setEditingTitle(e.target.value)}
            onBlur={onSaveRename}
            onKeyDown={(e) => e.key === "Enter" && onSaveRename()}
            autoFocus
            className="w-full bg-parchment-container-lowest border border-parchment-primary text-xs px-1 py-0.5 outline-none font-serif"
          />
        ) : (
          <span className="truncate">{conv.title}</span>
        )}
      </div>

      {!isEditing && (
        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={onPin}
            className={`p-1 hover:text-parchment-primary ${conv.isPinned ? "text-parchment-primary opacity-100" : ""}`}
            title={conv.isPinned ? "Unpin inquiry" : "Pin inquiry"}
          >
            <Pin className="w-2.5 h-2.5" />
          </button>
          <button onClick={onStartRename} className="p-1 hover:text-parchment-primary" title="Rename inquiry">
            <Edit2 className="w-2.5 h-2.5" />
          </button>
          <button onClick={onDelete} className="p-1 hover:text-parchment-error" title="Delete inquiry">
            <Trash2 className="w-2.5 h-2.5" />
          </button>
        </div>
      )}
    </div>
  );
}

