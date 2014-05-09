import java.io.*;
import java.net.*;
import java.nio.*;
import java.nio.channels.*;
import java.nio.charset.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.locks.*;

public class NotifyClient extends Thread {

	public interface Listener {
		public void onNotify(Object sender, String content);
	}

	private HashSet<Listener> m_listeners = new HashSet<Listener>();
	private Semaphore m_shutdown = new Semaphore(1);

	private SocketChannel m_channel;
	private Selector m_selector;
	private String m_userKey;
	private String m_host;
	private int m_port;

	public NotifyClient(String userKey, String host, int port) {
		this.m_userKey = userKey;
		this.m_host = host;
		this.m_port = port;
	}

	public void setUserKey(String userKey) {
		this.m_userKey = userKey;
	}

	public void shutdown(){
		m_shutdown.release();
	}

	protected void processPacket(int cmd, String body) {
		switch(cmd) {
			case 1: // hello
				break;
			case 3: // notify
				// parse body by json format
				fireNotifyEvent(body);
				break;
		}
	}

	public void run() {
		my_sleep(0); // first lock 

		while(true) { // always connect ...
			
			try{
				if (my_sleep(0)) {
					System.err.println("shutdown ...");
					break; // shutdown
				}
				work();
			} catch (java.net.PortUnreachableException e) {
				System.err.println("通知客户端连接服务器错误！10s后重连。");
				my_sleep(10000);
			} catch (java.net.ConnectException e) {
				System.err.println("通知客户端连接服务器错误！10s后重连。");
				my_sleep(10000);
			} catch(Exception e) {
				e.printStackTrace();
				my_sleep(10000);
			} finally {
				try { if (m_selector.isOpen()) { m_selector.close(); } } catch(Exception e) { e.printStackTrace(); }
			}
		}
	}    

	private void work() throws Exception {
		
		m_selector = Selector.open();
		System.out.println("通知客户端连接服务器...");

		// 开启一个通道 连接服务端
		m_channel = SocketChannel.open();
		m_channel.configureBlocking(false);
		m_channel.connect(new InetSocketAddress(m_host, m_port));
		m_channel.register(m_selector, SelectionKey.OP_CONNECT);

		ByteBuffer byteBuffer = ByteBuffer.allocate(4096); // buffer size???
		byteBuffer.order(ByteOrder.BIG_ENDIAN);

		while (true) { // always read data
			try {
				int n = m_selector.select();
				if (n > 0) {
					Iterator iterator = m_selector.selectedKeys().iterator();
					while (iterator.hasNext())
					{
						SelectionKey key = (SelectionKey) iterator.next();
						iterator.remove();
						//连接事件
						if(key.isConnectable()) {
							System.out.println("通知客户端发送注册信息...");

							SocketChannel socketChannel = (SocketChannel) key.channel();
							if(socketChannel.isConnectionPending())
								socketChannel.finishConnect();

							// 向服务器发注册信息
							ByteBuffer writeBuffer = ByteBuffer.allocate(512);
							writeBuffer.order(ByteOrder.BIG_ENDIAN);
							writeBuffer.put("NT".getBytes("UTF-8"));
							writeBuffer.putShort((short)2); // register
							writeBuffer.putShort((short)32); // userKey size
							writeBuffer.put(m_userKey.getBytes("UTF-8"));
							writeBuffer.flip();
							while(writeBuffer.hasRemaining())
								socketChannel.write(writeBuffer);

							// 等待读
							socketChannel.register(m_selector, SelectionKey.OP_READ);
						}

						if (key.isReadable()) {
							
							System.out.println("通知客户端读取数据包...");
							SocketChannel socketChannel = (SocketChannel) key.channel();
							
							int readed = socketChannel.read(byteBuffer);
							if (readed < 0)
								throw new java.net.ConnectException(); // error connect by reset


							ByteBuffer buffer = byteBuffer.asReadOnlyBuffer();
							buffer.flip();
							buffer.order(ByteOrder.BIG_ENDIAN);

							if (buffer.remaining() >= 6) { // has packet header
								byte[] sign = new byte[2];
								buffer.get(sign);

								if (0 == "NT".compareTo(new String(sign, "UTF-8"))) {
									short cmd = buffer.getShort();
									short size = buffer.getShort();

									if ( buffer.remaining() >= size ) {
										byte[] dataBuf = new byte[size];
										buffer.get(dataBuf);
										processPacket(cmd, new String(dataBuf, "UTF-8"));
										byteBuffer.clear(); // reset buffer
									}
								} else {
									byteBuffer.clear(); // buffer error && reset buffer
								}

							}
								
							// 继续等待读
							// socketChannel.register(m_selector, SelectionKey.OP_READ);
						}
					}
				} else {
					throw new Exception("通知客户端读取数据超时！");
				}
			} catch (Exception e) {
				throw e;
			}
		}
	}

	public void addListener(Listener listener) {
		m_listeners.add(listener);
	}
	public void removeListener(Listener listener) {
		m_listeners.remove(listener);
	}
	private void fireNotifyEvent(String content) {
		Iterator<Listener> itr = m_listeners.iterator();
		while (itr.hasNext()) {
			Listener listener = (Listener) itr.next();
			listener.onNotify(this, content);
		}
	}

	private void debug_data(ByteBuffer byteBuffer, int readed){
		System.out.println("read data size: " + readed);
		byte[] ffff = byteBuffer.array();
		for (byte b : ffff) {
			System.out.print(String.format(" 0x%02X", b));
		}
		System.out.println("");
	}

	private boolean my_sleep(long milliseconds) {
		try { return m_shutdown.tryAcquire(milliseconds, TimeUnit.MILLISECONDS); } catch (Exception e) { return false; }
	}

	public static void main(String[] args) throws Exception {
		NotifyClient t = new NotifyClient("5ccef621ab6f4fe9a27b2f1b467bf040", "127.0.0.1", 9002);
		t.addListener(new Listener(){
			public void onNotify(Object sender, String content) {
				System.out.println("=========================================");
				System.out.println(content);
			}
		});
		t.start();
		t.join();
	}
}
