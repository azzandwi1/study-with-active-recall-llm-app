"use client"

import { motion } from "framer-motion"

export function ReviewCalendar() {
  // Mock data for the last 30 days
  const days = Array.from({ length: 30 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (29 - i))
    const activity = Math.random() > 0.3 ? Math.floor(Math.random() * 4) + 1 : 0
    return {
      date,
      activity,
      day: date.getDate(),
    }
  })

  const getActivityColor = (activity: number) => {
    if (activity === 0) return "bg-muted"
    if (activity === 1) return "bg-primary/20"
    if (activity === 2) return "bg-primary/40"
    if (activity === 3) return "bg-primary/60"
    return "bg-primary"
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-7 gap-1">
        {["M", "S", "S", "R", "K", "J", "S"].map((day, i) => (
          <div key={i} className="text-xs text-muted-foreground text-center p-1">
            {day}
          </div>
        ))}

        {days.map((day, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2, delay: i * 0.01 }}
            className={`aspect-square rounded-sm ${getActivityColor(day.activity)} flex items-center justify-center`}
            title={`${day.date.toLocaleDateString("id-ID")} - ${day.activity} review`}
          >
            <span className="text-xs text-foreground/70">{day.day}</span>
          </motion.div>
        ))}
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Kurang</span>
        <div className="flex gap-1">
          <div className="w-3 h-3 rounded-sm bg-muted"></div>
          <div className="w-3 h-3 rounded-sm bg-primary/20"></div>
          <div className="w-3 h-3 rounded-sm bg-primary/40"></div>
          <div className="w-3 h-3 rounded-sm bg-primary/60"></div>
          <div className="w-3 h-3 rounded-sm bg-primary"></div>
        </div>
        <span>Lebih</span>
      </div>
    </div>
  )
}
