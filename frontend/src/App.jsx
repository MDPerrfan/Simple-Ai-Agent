import { useEffect, useRef, useState } from "react";
import {
  Bot,
  ChefHat,
  Clock3,
  Compass,
  MapPin,
  Menu,
  MessageSquarePlus,
  Send,
  Sparkles,
  Utensils,
  X,
} from "lucide-react";

const suggestions = [
  {
    icon: MapPin,
    title: "Nearby restaurants",
    action: "location",
  },
  {
    icon: Clock3,
    title: "Open late",
    prompt: "Find Indian restaurants near KL Sentral that stay open late",
  },
  {
    icon: Utensils,
    title: "Explore a cuisine",
    prompt: "Find Chinese restaurants near GEC Circle, Chittagong",
  },
];

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const findNearbyRestaurants = () => {
  if (!navigator.geolocation) {
    alert("Location is not supported by your browser.");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const { latitude, longitude } = position.coords;

      const message = "Find restaurants near my current location";

      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: "📍 Find restaurants near me",
        },
      ]);

      setLoading(true);

      try {
        const response = await fetch(
          "http://127.0.0.1:8000/chat",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },

            body: JSON.stringify({
              message,
              latitude,
              longitude,
            }),
          }
        );

        const data = await response.json();

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              data.answer ||
              data.error ||
              "I couldn't find nearby restaurants.",
          },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              "I couldn't connect to the dining service.",
          },
        ]);
      } finally {
        setLoading(false);
      }
    },

    () => {
      alert(
        "Location access was denied. You can type your city or area instead."
      );
    },

    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 300000,
    }
  );
};

  const sendMessage = async (text = input) => {
    const message = text.trim();

    if (!message || loading) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: message,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Request failed.");
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            data.answer ||
            "I couldn't find an answer for that request.",
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I couldn't connect to the dining service. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const newChat = () => {
    setMessages([]);
    setInput("");
    setSidebarOpen(false);
  };

  return (
    <div className="h-dvh overflow-hidden bg-slate-50 text-slate-950">
      <div className="flex h-full">

        {/* Mobile overlay */}
        {sidebarOpen && (
          <button
            aria-label="Close sidebar"
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-30 bg-slate-950/30 backdrop-blur-sm lg:hidden"
          />
        )}

        {/* Sidebar */}
        <aside
          className={`
            fixed inset-y-0 left-0 z-40 flex w-72 flex-col
            border-r border-slate-200 bg-white p-4
            transition-transform duration-300
            lg:static lg:translate-x-0
            ${sidebarOpen
              ? "translate-x-0"
              : "-translate-x-full"
            }
          `}
        >
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-orange-500 text-white shadow-sm">
                <ChefHat size={21} />
              </div>

              <div>
                <h1 className="font-bold tracking-tight">
                  DineAI
                </h1>
                <p className="text-xs text-slate-500">
                  Dining Assistant
                </p>
              </div>
            </div>

            <button
              onClick={() => setSidebarOpen(false)}
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
            >
              <X size={19} />
            </button>
          </div>

          <button
            onClick={newChat}
            className="flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
          >
            <MessageSquarePlus size={17} />
            New conversation
          </button>

          <div className="mt-8">
            <p className="mb-3 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Try asking
            </p>

            <div className="space-y-1">
              {suggestions.map((item) => {
                const Icon = item.icon;

                return (
                  <button
                    key={item.title}
                    onClick={() => {
                      if (item.action === "location") {
                        findNearbyRestaurants();
                      } else {
                        sendMessage(item.prompt);
                      }

                      setSidebarOpen(false);
                    }}
                    className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
                  >
                    <Icon size={17} />
                    {item.title}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-auto rounded-2xl border border-orange-100 bg-orange-50 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-orange-900">
              <Compass size={16} />
              Live discovery
            </div>

            <p className="text-xs leading-5 text-orange-800/70">
              Restaurant information is retrieved from
              OpenStreetMap and may be incomplete.
            </p>
          </div>
        </aside>

        {/* Main app */}
        <main className="flex min-w-0 flex-1 flex-col">

          {/* Header */}
          <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur md:px-7">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="rounded-lg p-2 hover:bg-slate-100 lg:hidden"
              >
                <Menu size={20} />
              </button>

              <div>
                <p className="text-sm font-semibold">
                  AI Dining Assistant
                </p>

                <div className="flex items-center gap-1.5 text-xs text-slate-500">
                  <span className="size-2 rounded-full bg-emerald-500" />
                  Agent online
                </div>
              </div>
            </div>

            <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-500 sm:flex">
              <Sparkles size={14} className="text-orange-500" />
              Live restaurant discovery
            </div>
          </header>

          {/* Conversation */}
          <section className="flex-1 overflow-y-auto">
            <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col px-4 py-8 md:px-8">

              {/* Empty state */}
              {messages.length === 0 && (
                <div className="my-auto py-10">
                  <div className="mx-auto max-w-2xl text-center">

                    <div className="mx-auto mb-5 flex size-14 items-center justify-center rounded-2xl bg-orange-500 text-white shadow-lg shadow-orange-500/20">
                      <ChefHat size={27} />
                    </div>

                    <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
                      Where should we eat?
                    </h2>

                    <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-500 md:text-base">
                      Tell me a location, cuisine, or dining
                      preference and I'll search live restaurant
                      data for you.
                    </p>
                  </div>

                  <div className="mx-auto mt-9 grid max-w-3xl gap-3 md:grid-cols-3">
                    {suggestions.map((item) => {
                      const Icon = item.icon;

                      return (
                        <button
                          key={item.title}
                          onClick={() => {
                            if (item.action === "location") {
                              findNearbyRestaurants();
                            } else {
                              sendMessage(item.prompt);
                            }
                          }}
                          className="group rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-orange-200 hover:shadow-md"
                        >
                          <div className="mb-4 flex size-9 items-center justify-center rounded-xl bg-orange-50 text-orange-600">
                            <Icon size={18} />
                          </div>

                          <p className="text-sm font-semibold">
                            {item.title}
                          </p>

                          <p className="mt-1.5 text-xs leading-5 text-slate-500">
                            {item.prompt}
                          </p>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Messages */}
              {messages.length > 0 && (
                <div className="space-y-7 pb-5">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex gap-3 ${message.role === "user"
                        ? "justify-end"
                        : "justify-start"
                        }`}
                    >
                      {message.role === "assistant" && (
                        <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-orange-500 text-white">
                          <Bot size={18} />
                        </div>
                      )}

                      <div
                        className={`
                          max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3
                          text-sm leading-6 md:max-w-[75%]
                          ${message.role === "user"
                            ? "rounded-br-md bg-slate-950 text-white"
                            : "rounded-bl-md border border-slate-200 bg-white text-slate-700 shadow-sm"
                          }
                        `}
                      >
                        {message.content}
                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="flex items-center gap-3">
                      <div className="flex size-9 items-center justify-center rounded-xl bg-orange-500 text-white">
                        <Bot size={18} />
                      </div>

                      <div className="flex items-center gap-1 rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-4 shadow-sm">
                        {[0, 1, 2].map((item) => (
                          <span
                            key={item}
                            className="size-1.5 animate-bounce rounded-full bg-slate-400"
                            style={{
                              animationDelay: `${item * 120}ms`,
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  <div ref={bottomRef} />
                </div>
              )}
            </div>
          </section>

          {/* Composer */}
          <footer className="shrink-0 border-t border-slate-200 bg-white px-4 py-4 md:px-8">
            <div className="mx-auto max-w-4xl">
              <div className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-2 transition focus-within:border-orange-300 focus-within:ring-4 focus-within:ring-orange-100">
                <textarea
                  value={input}
                  rows={1}
                  placeholder="Ask DineAI about restaurants..."
                  onChange={(e) =>
                    setInput(e.target.value)
                  }
                  onKeyDown={(e) => {
                    if (
                      e.key === "Enter" &&
                      !e.shiftKey
                    ) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                  className="max-h-32 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-sm outline-none placeholder:text-slate-400"
                />

                <button
                  onClick={() => sendMessage()}
                  disabled={!input.trim() || loading}
                  className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-orange-500 text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Send size={18} />
                </button>
              </div>

              <p className="mt-2 text-center text-[11px] text-slate-400">
                Restaurant information may be incomplete. Verify
                important details before visiting.
              </p>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}

export default App;