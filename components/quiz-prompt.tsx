"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { VerdictBadge } from "@/components/verdict-badge"
import { ArrowRight } from "lucide-react"
import { motion } from "framer-motion"
import { useToast } from "@/hooks/use-toast"
import { apiRequest } from "@/lib/api"

interface QuizPromptProps {
  question: {
    id: string
    question: string
    correctAnswer: string
    difficulty: "easy" | "medium" | "hard"
  }
  currentIndex: number
  totalQuestions: number
  onNext: () => void
  onComplete: () => void
}

export function QuizPrompt({ question, currentIndex, totalQuestions, onNext, onComplete }: QuizPromptProps) {
  const [userAnswer, setUserAnswer] = useState("")
  const [isChecking, setIsChecking] = useState(false)
  const [verdict, setVerdict] = useState<{ correct: boolean; feedback: string } | null>(null)
  const { toast } = useToast()

  const difficultyColors = {
    easy: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300",
    medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300",
    hard: "bg-rose-100 text-rose-700 dark:bg-rose-900/20 dark:text-rose-300",
  }

  const handleSubmit = async () => {
    if (!userAnswer.trim()) {
      toast({
        title: "Jawaban Kosong",
        description: "Silakan masukkan jawaban Anda",
        variant: "destructive",
      })
      return
    }

    setIsChecking(true)

    try {
      const response = await apiRequest("/api/v1/quiz/check", {
        method: "POST",
        body: JSON.stringify({
          questionId: question.id,
          userAnswer: userAnswer.trim(),
          correctAnswer: question.correctAnswer,
        }),
      })

      setVerdict({
        correct: response.correct,
        feedback: response.feedback,
      })
    } catch (error) {
      // Fallback evaluation for demo
      const isCorrect = userAnswer.toLowerCase().includes(question.correctAnswer.toLowerCase().substring(0, 10))
      setVerdict({
        correct: isCorrect,
        feedback: isCorrect
          ? "Jawaban Anda benar! Pemahaman yang baik."
          : "Jawaban kurang tepat. Mari review kembali materi ini.",
      })
    } finally {
      setIsChecking(false)
    }
  }

  const handleNext = () => {
    if (currentIndex + 1 >= totalQuestions) {
      onComplete()
    } else {
      onNext()
      setUserAnswer("")
      setVerdict(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Progress */}
      <div className="flex items-center justify-between">
        <Badge variant="outline" className="rounded-lg">
          Soal {currentIndex + 1} dari {totalQuestions}
        </Badge>
        <Badge className={`rounded-lg ${difficultyColors[question.difficulty]}`}>
          {question.difficulty === "easy" ? "Mudah" : question.difficulty === "medium" ? "Sedang" : "Sulit"}
        </Badge>
      </div>

      {/* Question Card */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <Card className="rounded-2xl border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="text-lg text-foreground">Pertanyaan</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-base text-foreground leading-relaxed mb-6">{question.question}</p>

            <div className="space-y-4">
              <Textarea
                placeholder="Ketik jawaban Anda di sini..."
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                className="min-h-[120px] rounded-xl resize-none"
                disabled={!!verdict}
              />

              {!verdict ? (
                <Button
                  onClick={handleSubmit}
                  disabled={isChecking || !userAnswer.trim()}
                  className="w-full rounded-xl"
                >
                  {isChecking ? "Memeriksa..." : "Periksa Jawaban"}
                </Button>
              ) : (
                <div className="space-y-4">
                  <VerdictBadge correct={verdict.correct} feedback={verdict.feedback} />

                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.2 }}
                  >
                    <Card className="rounded-xl bg-muted/50">
                      <CardContent className="p-4">
                        <h4 className="font-medium text-foreground mb-2">Jawaban yang Benar:</h4>
                        <p className="text-sm text-muted-foreground leading-relaxed">{question.correctAnswer}</p>
                      </CardContent>
                    </Card>
                  </motion.div>

                  <Button onClick={handleNext} className="w-full rounded-xl gap-2">
                    {currentIndex + 1 >= totalQuestions ? "Selesai" : "Soal Berikutnya"}
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
