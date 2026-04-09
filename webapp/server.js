const { createServer } = require('http')
const { Server } = require('socket.io')
const next = require('next')

const dev = process.env.NODE_ENV !== 'production'
const hostname = '0.0.0.0'
const port = parseInt(process.env.PORT || '3000', 10)

const app = next({ dev, hostname, port })
const handler = app.getRequestHandler()

app.prepare().then(() => {
  const httpServer = createServer(handler)

  const io = new Server(httpServer, {
    path: '/api/socket',
    cors: { origin: '*' },
    transports: ['websocket', 'polling'],
  })

  io.on('connection', (socket) => {
    console.log('Socket connected:', socket.id)

    socket.on('join-room', (roomId) => {
      socket.join(roomId)
    })

    socket.on('leave-room', (roomId) => {
      socket.leave(roomId)
    })

    socket.on('send-message', ({ roomId, message }) => {
      // Broadcast to all OTHER users in the room
      socket.to(roomId).emit('message', message)
    })

    socket.on('typing', ({ roomId, userId }) => {
      socket.to(roomId).emit('typing', userId)
    })

    socket.on('stop-typing', ({ roomId, userId }) => {
      socket.to(roomId).emit('stop-typing', userId)
    })

    socket.on('disconnect', () => {
      console.log('Socket disconnected:', socket.id)
    })
  })

  httpServer.listen(port, hostname, () => {
    console.log(`> IsDiscipline ready on http://${hostname}:${port}`)
  })
})
