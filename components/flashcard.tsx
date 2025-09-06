"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ChevronLeft, ChevronRight, RotateCcw, Check, X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface FlashcardProps {
  card: {
    id: string
    question: string
    answer: string
    difficulty: "easy" | "medium" | "hard"
    mastered: boolean
  }
  onNext: () => void
  onPrevious: () => void
  onMastery: (cardId: string, mastered: boolean) => void
  currentIndex: number
  totalCards: number
}

export function Flashcard({ card, onNext, onPrevious, onMastery, currentIndex, totalCards }: FlashcardProps) {
  const [isFlipped, setIsFlipped] = useState(false)
  const [showResult, setShowResult] = useState(false)

  const difficultyColors = {
    easy: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300",
    medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300",
    hard: "bg-rose-100 text-rose-700 dark:bg-rose-900/20 dark:text-rose-300",
  }

  const handleFlip = () => {
    setIsFlipped(!isFlipped)
    if (!isFlipped) {
      setShowResult(true)
    }
  }

  const handleMastery = (mastered: boolean) => {
    onMastery(card.id, mastered)
    setTimeout(() => {
      onNext()
      setIsFlipped(false)
      setShowResult(false)
    }, 500)
  }

  const handleNext = () => {
    onNext()
    setIsFlipped(false)
    setShowResult(false)
  }

  const handlePrevious = () => {
    onPrevious()
    setIsFlipped(false)
    setShowResult(false)
  }

  return (
    <div className="space-y-6">
      {/* Card Counter */}
      <div className="flex items-center justify-between">
        <Badge variant="outline" className="rounded-lg">
          {currentIndex + 1} dari {totalCards}
        </Badge>
        <Badge className={`rounded-lg ${difficultyColors[card.difficulty]}`}>
          {card.difficulty === "easy" ? "Mudah" : card.difficulty === "medium" ? "Sedang" : "Sulit"}
        </Badge>
      </div>

      {/* Flashcard */}
      <div className="relative h-80">
        <AnimatePresence mode="wait">
          <motion.div
            key={isFlipped ? "answer" : "question"}
            initial={{ rotateY: 90, opacity: 0 }}
            animate={{ rotateY: 0, opacity: 1 }}
            exit={{ rotateY: -90, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-0"
          >
            <Card
              className="h-full rounded-2xl border-0 shadow-lg cursor-pointer hover:shadow-xl transition-all duration-300"
              onClick={handleFlip}
            >
              <CardContent className="h-full flex items-center justify-center p-8">
                <div className="text-center space-y-4">
                  {!isFlipped ? (
                    <>
                      <h3 className="text-xl font-semibold text-foreground mb-4">Pertanyaan</h3>
                      <p className="text-lg text-foreground leading-relaxed">{card.question}</p>
                      <p className="text-sm text-muted-foreground mt-6">Klik untuk melihat jawaban</p>
                    </>
                  ) : (
                    <>
                      <h3 className="text-xl font-semibold text-primary mb-4">Jawaban</h3>
                      <p className="text-base text-foreground leading-relaxed">{card.answer}</p>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={handlePrevious} className="rounded-xl gap-2 bg-transparent">
          <ChevronLeft className="h-4 w-4" />
          Sebelumnya
        </Button>

        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={handleFlip} className="rounded-xl gap-2">
            <RotateCcw className="h-4 w-4" />
            Balik
          </Button>
        </div>

        <Button variant="outline" onClick={handleNext} className="rounded-xl gap-2 bg-transparent">
          Selanjutnya
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Mastery Controls */}
      <AnimatePresence>
        {showResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="space-y-4"
          >
            <p className="text-center text-muted-foreground">Seberapa baik Anda memahami kartu ini?</p>
            <div className="flex gap-3">
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className="flex-1">
                <Button
                  variant="outline"
                  onClick={() => handleMastery(false)}
                  className="w-full rounded-xl gap-2 border-rose-200 hover:bg-rose-50 dark:border-rose-800 dark:hover:bg-rose-950/20"
                >
                  <X className="h-4 w-4 text-rose-500" />
                  Perlu Review
                </Button>
              </motion.div>
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className="flex-1">
                <Button
                  onClick={() => handleMastery(true)}
                  className="w-full rounded-xl gap-2 bg-emerald-600 hover:bg-emerald-700"
                >
                  <Check className="h-4 w-4" />
                  Sudah Dikuasai
                </Button>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
