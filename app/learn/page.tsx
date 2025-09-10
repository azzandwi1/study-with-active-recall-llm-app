"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Brain, ArrowLeft, BookOpen, Target, Calendar, Settings } from "lucide-react"
import Link from "next/link"
import { motion } from "framer-motion"
import { ApiKeyGate } from "@/components/api-key-gate"
import { Flashcard } from "@/components/flashcard"
import { QuizPrompt } from "@/components/quiz-prompt"
import { ProgressRing } from "@/components/progress-ring"
import { ReviewCalendar } from "@/components/review-calendar"
import { useToast } from "@/hooks/use-toast"
import { apiRequest } from "@/lib/api"

interface FlashcardData {
  id: string
  question: string
  answer: string
  difficulty: "easy" | "medium" | "hard"
  mastered: boolean
}

interface QuizQuestion {
  card_id: string
  question: string
  difficulty: "easy" | "medium" | "hard"
  tags: string[]
}

interface LearningStats {
  totalCards: number
  masteredCards: number
  dailyStreak: number
  todayReviewed: number
}

export default function LearnPage() {
  const [activeMode, setActiveMode] = useState<"flashcards" | "quiz">("flashcards")
  const [quizLength, setQuizLength] = useState("10")
  const [flashcards, setFlashcards] = useState<FlashcardData[]>([])
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([])
  const [currentQuizIndex, setCurrentQuizIndex] = useState(0)
  const [quizActive, setQuizActive] = useState(false)
  const [stats, setStats] = useState<LearningStats>({
    totalCards: 0,
    masteredCards: 0,
    dailyStreak: 7,
    todayReviewed: 0,
  })
  const { toast } = useToast()

  useEffect(() => {
    loadFlashcards()
    loadStats()
  }, [])

  const loadFlashcards = async () => {
    try {
      // Get the latest collection from localStorage (set during ingest)
      const latestCollectionId = localStorage.getItem('latest_collection_id')
      
      if (latestCollectionId) {
        try {
          const response = await apiRequest(`/api/v1/generate/flashcards/${latestCollectionId}`)
          if (response.flashcards && response.flashcards.length > 0) {
            const apiFlashcards: FlashcardData[] = response.flashcards.map((card: any) => ({
              id: card.id,
              question: card.question,
              answer: card.answer,
              difficulty: card.difficulty,
              mastered: false, // This would come from user progress in a real app
            }))
            setFlashcards(apiFlashcards)
            setStats((prev) => ({
              ...prev,
              totalCards: apiFlashcards.length,
              masteredCards: apiFlashcards.filter((c) => c.mastered).length,
            }))
            return
          }
        } catch (apiError) {
          console.log("No flashcards found for latest collection, using mock data")
        }
      } else {
        console.log("No collection ID found, using mock data")
      }
      
      // Fallback to mock data if API fails
      const mockFlashcards: FlashcardData[] = [
        {
          id: "1",
          question: "Apa itu Active Recall?",
          answer:
            "Active Recall adalah teknik pembelajaran yang melibatkan upaya aktif untuk mengingat informasi dari memori, bukan hanya membaca ulang materi.",
          difficulty: "medium",
          mastered: false,
        },
        {
          id: "2",
          question: "Mengapa Active Recall efektif?",
          answer:
            "Active Recall efektif karena memperkuat jalur neural dan meningkatkan retensi memori jangka panjang melalui proses retrieval yang berulang.",
          difficulty: "hard",
          mastered: true,
        },
        {
          id: "3",
          question: "Kapan sebaiknya menggunakan flashcard?",
          answer:
            "Flashcard sebaiknya digunakan untuk menghafal fakta, definisi, rumus, atau konsep-konsep kunci yang perlu diingat dengan cepat.",
          difficulty: "easy",
          mastered: false,
        },
      ]
      setFlashcards(mockFlashcards)
      setStats((prev) => ({
        ...prev,
        totalCards: mockFlashcards.length,
        masteredCards: mockFlashcards.filter((c) => c.mastered).length,
      }))
    } catch (error) {
      toast({
        title: "Error",
        description: "Gagal memuat flashcard",
        variant: "destructive",
      })
    }
  }

  const loadStats = () => {
    // Mock stats - in real app, this would come from API
    setStats((prev) => ({ ...prev, todayReviewed: 12 }))
  }

  const startQuiz = async () => {
    try {
      // Get the latest collection from localStorage (set during ingest)
      const latestCollectionId = localStorage.getItem('latest_collection_id')
      
      if (!latestCollectionId) {
        toast({
          title: "Error",
          description: "Tidak ada koleksi tersedia. Silakan buat flashcard terlebih dahulu.",
          variant: "destructive",
        })
        return
      }
      
      const response = await apiRequest("/api/v1/quiz/start", {
        method: "POST",
        body: JSON.stringify({
          collection_id: latestCollectionId,
          count: Number.parseInt(quizLength),
          strategy: "mixed",
          user_id: "default_user",
        }),
      })

      setQuizQuestions(response.questions || [])
      setCurrentQuizIndex(0)
      setQuizActive(true)
      setActiveMode("quiz")
    } catch (error) {
      toast({
        title: "Error",
        description: "Gagal memulai kuis",
        variant: "destructive",
      })
    }
  }

  const handleCardMastery = (cardId: string, mastered: boolean) => {
    setFlashcards((prev) => prev.map((card) => (card.id === cardId ? { ...card, mastered } : card)))
    setStats((prev) => ({
      ...prev,
      masteredCards: flashcards.filter((c) => c.mastered || (c.id === cardId && mastered)).length,
    }))
  }

  const nextCard = () => {
    setCurrentCardIndex((prev) => (prev + 1) % flashcards.length)
  }

  const prevCard = () => {
    setCurrentCardIndex((prev) => (prev - 1 + flashcards.length) % flashcards.length)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Kembali
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <Brain className="h-8 w-8 text-primary" />
              <span className="text-2xl font-bold text-foreground">Active Recall</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/ingest">
              <Button variant="outline" size="sm">
                Tambah Materi
              </Button>
            </Link>
            <Link href="/settings">
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </nav>
      </header>

      <main className="container mx-auto px-4 py-8">
        <ApiKeyGate>
          <div className="grid lg:grid-cols-4 gap-8">
            {/* Main Learning Area */}
            <div className="lg:col-span-3 space-y-6">
              {/* Mode Selection */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
                <Card className="rounded-2xl border-0 shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-primary" />
                      Mode Pembelajaran
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Tabs value={activeMode} onValueChange={(value) => setActiveMode(value as "flashcards" | "quiz")}>
                      <TabsList className="grid w-full grid-cols-2 rounded-xl">
                        <TabsTrigger value="flashcards" className="gap-2 rounded-lg">
                          <BookOpen className="h-4 w-4" />
                          Flashcard
                        </TabsTrigger>
                        <TabsTrigger value="quiz" className="gap-2 rounded-lg">
                          <Target className="h-4 w-4" />
                          Kuis
                        </TabsTrigger>
                      </TabsList>

                      <TabsContent value="flashcards" className="mt-6">
                        {flashcards.length > 0 && (
                          <Flashcard
                            card={flashcards[currentCardIndex]}
                            onNext={nextCard}
                            onPrevious={prevCard}
                            onMastery={handleCardMastery}
                            currentIndex={currentCardIndex}
                            totalCards={flashcards.length}
                          />
                        )}
                      </TabsContent>

                      <TabsContent value="quiz" className="mt-6">
                        {!quizActive ? (
                          <div className="space-y-6">
                            <div className="text-center space-y-4">
                              <h3 className="text-xl font-semibold text-foreground">Mulai Kuis Adaptif</h3>
                              <p className="text-muted-foreground">Pilih jumlah soal dan uji pemahaman Anda</p>
                            </div>

                            <div className="space-y-4">
                              <Label className="text-base font-medium">Jumlah Soal</Label>
                              <RadioGroup value={quizLength} onValueChange={setQuizLength} className="flex gap-6">
                                <div className="flex items-center space-x-2">
                                  <RadioGroupItem value="5" id="quiz-5" />
                                  <Label htmlFor="quiz-5">5 Soal</Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <RadioGroupItem value="10" id="quiz-10" />
                                  <Label htmlFor="quiz-10">10 Soal</Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <RadioGroupItem value="15" id="quiz-15" />
                                  <Label htmlFor="quiz-15">15 Soal</Label>
                                </div>
                              </RadioGroup>
                            </div>

                            <Button onClick={startQuiz} size="lg" className="w-full rounded-xl">
                              Mulai Kuis ({quizLength} Soal)
                            </Button>
                          </div>
                        ) : (
                          <QuizPrompt
                            question={quizQuestions[currentQuizIndex]}
                            currentIndex={currentQuizIndex}
                            totalQuestions={quizQuestions.length}
                            onComplete={() => {
                              setQuizActive(false)
                              toast({
                                title: "Kuis Selesai!",
                                description: "Bagus! Anda telah menyelesaikan kuis.",
                              })
                            }}
                            onNext={() => setCurrentQuizIndex((prev) => prev + 1)}
                          />
                        )}
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Progress Overview */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
              >
                <Card className="rounded-2xl border-0 shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-lg">Progress Hari Ini</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <ProgressRing
                      progress={(stats.masteredCards / Math.max(stats.totalCards, 1)) * 100}
                      size={120}
                      strokeWidth={8}
                    />

                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Dikuasai</span>
                        <span className="font-semibold text-foreground">
                          {stats.masteredCards}/{stats.totalCards}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Streak</span>
                        <span className="font-semibold text-accent">{stats.dailyStreak} hari</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Hari ini</span>
                        <span className="font-semibold text-primary">{stats.todayReviewed} kartu</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Review Calendar */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <Card className="rounded-2xl border-0 shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      Kalender Review
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ReviewCalendar />
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </div>
        </ApiKeyGate>
      </main>
    </div>
  )
}
