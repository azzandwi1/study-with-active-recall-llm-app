"use client"

import { CheckCircle, XCircle } from "lucide-react"
import { motion } from "framer-motion"

interface VerdictBadgeProps {
  correct: boolean
  feedback: string
}

export function VerdictBadge({ correct, feedback }: VerdictBadgeProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{
        opacity: 1,
        scale: 1,
        x: correct ? 0 : [-2, 2, -2, 2, 0], // Shake animation for incorrect
      }}
      transition={{
        duration: correct ? 0.3 : 0.5,
        x: { duration: 0.4 },
      }}
      className={`p-4 rounded-xl border ${
        correct
          ? "bg-emerald-50 border-emerald-200 dark:bg-emerald-950/20 dark:border-emerald-800"
          : "bg-rose-50 border-rose-200 dark:bg-rose-950/20 dark:border-rose-800"
      }`}
    >
      <div className="flex items-start gap-3">
        {correct ? (
          <CheckCircle className="h-5 w-5 text-emerald-600 mt-0.5 flex-shrink-0" />
        ) : (
          <XCircle className="h-5 w-5 text-rose-600 mt-0.5 flex-shrink-0" />
        )}
        <div>
          <h4
            className={`font-medium mb-1 ${
              correct ? "text-emerald-700 dark:text-emerald-300" : "text-rose-700 dark:text-rose-300"
            }`}
          >
            {correct ? "Benar!" : "Kurang Tepat"}
          </h4>
          <p
            className={`text-sm leading-relaxed ${
              correct ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
            }`}
          >
            {feedback}
          </p>
        </div>
      </div>
    </motion.div>
  )
}
